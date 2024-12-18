""" Konvertierungsmodul von 1.9x nach software2
Konvertiert die Lade- und Tages-Log-Dateien von csv nach json.
Falls nötig, ohne Abhängigkeit zur sonstigen software2-Implementierung.
"""

import csv
from dataclasses import asdict
import datetime
from functools import reduce
from itertools import groupby
import json
import logging
from operator import itemgetter
import os
import pathlib
import shutil
import tarfile
from threading import Thread
from typing import Callable, Dict, List, Optional, Union

from control import data
from control.ev import ev
from dataclass_utils import dataclass_from_dict
import dataclass_utils
from helpermodules.data_migration.id_mapping import MapId
from helpermodules.hardware_configuration import update_hardware_configuration
from helpermodules.measurement_logging.process_log import get_totals, string_to_float, string_to_int
from helpermodules.measurement_logging.write_log import LegacySmartHomeLogData, get_names
from helpermodules.timecheck import convert_timedelta_to_time_string, get_difference
from helpermodules.utils import joined_thread_handler
from helpermodules.pub import Pub
from helpermodules.utils.json_file_handler import write_and_check
from modules.ripple_control_receivers.gpio.config import GpioRcr
import re

log = logging.getLogger("data_migration")


def get_rounding_function_by_digits(digits: Union[int, None]) -> Callable:
    if digits is None:
        return lambda value: value
    elif digits == 0:
        return int
    else:
        return lambda value: round(value, digits)


class StreamArray(list):
    """
    Converts a generator into a list object that can be json serialized
    while still retaining the iterative nature of a generator.

    IE. It converts it to a list without having to exhaust the generator
    and keep it's contents in memory.
    """

    def __init__(self, generator):
        self.generator = generator
        self._len = 1

    def __iter__(self):
        self._len = 0
        for item in self.generator:
            yield item
            self._len += 1

    def __len__(self):
        """
        Json parser looks for a this method to confirm whether or not it can
        be parsed
        """
        return self._len


class MigrateData:
    MAJOR_VERSION = 1
    MINOR_VERSION = 9
    PATCH_VERSION = 303
    BACKUP_DATA_PATH = "./data/data_migration/var/www/html/openWB/web/logging/data"

    def __init__(self, id_map: Dict) -> None:
        self.id_map = dataclass_from_dict(MapId, id_map)

    def migrate(self):
        try:
            log.info("Datenmigration gestartet")
            log.info("Sicherungsdatei wird entpackt...")
            self._extract()
            log.info("Version wird geprüft...")
            self._check_version()
            log.info("Logdateien werden importiert...")
            joined_thread_handler(self.convert_csv_to_json_chargelog(), None)
            joined_thread_handler(self.convert_csv_to_json_measurement_log("daily"), None)
            joined_thread_handler(self.convert_csv_to_json_measurement_log("monthly"), None)
            log.info("Seriennummer wird übernommen...")
            self._migrate_settings_from_openwb_conf()
        except Exception as e:
            raise e
        finally:
            log.info("Temporäre Dateien werden entfernt...")
            self._remove_migration_data()
        log.info("Datenmigration beendet")

    def _check_version(self):
        with open("./data/data_migration/var/www/html/openWB/web/version") as f:
            version = f.read().replace("\n", "")
            sub_version = version.split(".")
        if not (int(sub_version[0]) > self.MAJOR_VERSION or (
            (int(sub_version[0]) == self.MAJOR_VERSION) and (
                (int(sub_version[1]) > self.MINOR_VERSION) or
                ((int(sub_version[1]) == self.MINOR_VERSION) and
                 (int(sub_version[2]) >= self.PATCH_VERSION))
            )
        )):
            self._remove_migration_data()
            raise ValueError(f"Das Backup für die Datenübernahme muss mindestens mit Version {self.MAJOR_VERSION}."
                             f"{self.MINOR_VERSION}.{self.PATCH_VERSION} erstellt worden sein. "
                             f"Backup-Version ist {version}.")

    def _remove_migration_data(self):
        shutil.rmtree("./data/data_migration/var")
        os.remove("./data/data_migration/data_migration.tar.gz")

    def map_to_new_ids(self, old_id: str) -> int:
        return getattr(self.id_map, old_id)

    def _file_to_extract_generator(self, members, log_folder_name: str):
        for tarinfo in members:
            if tarinfo.name.startswith(f"var/www/html/openWB/web/logging/data/{log_folder_name}"):
                yield tarinfo

    def _extract_files(self, log_folder_name: str):
        with tarfile.open('./data/data_migration/data_migration.tar.gz') as tar:
            tar.extractall(members=self._file_to_extract_generator(
                tar, log_folder_name), path="./data/data_migration")

    def _extract(self):
        self._extract_files("ladelog")
        self._extract_files("daily")
        self._extract_files("monthly")
        with tarfile.open('./data/data_migration/data_migration.tar.gz') as tar:
            tar.extract(member="var/www/html/openWB/openwb.conf", path="./data/data_migration")
            tar.extract(member="var/www/html/openWB/web/version", path="./data/data_migration")

    def convert_csv_to_json_chargelog(self) -> List[Thread]:
        """ konvertiert die alten Lade-Log-Dateien in das neue Format für 2.x.
        """
        def convert(old_file_name: str) -> None:
            try:
                new_entries = self._charge_log_file_entries(old_file_name)
                filepath = f"./data/charge_log/{old_file_name[:-4]}.json"
                content = []
                try:
                    with open(filepath, "r") as jsonFile:
                        content = json.load(jsonFile)
                except FileNotFoundError:
                    pass
                new_entries.extend(content)
                write_and_check(filepath, new_entries)
            except Exception:
                log.exception(f"Fehler beim Konvertieren des Lade-Logs vom {old_file_name}")

        pathlib.Path('./data/charge_log').mkdir(mode=0o755, parents=True, exist_ok=True)
        threads: List[Thread] = []
        for old_file_name in os.listdir(f"{self.BACKUP_DATA_PATH}/ladelog"):
            threads.append(Thread(target=convert, args=[old_file_name, ], name=f"chargelog {old_file_name}"))
        return threads

    def _charge_log_file_entries(self, file: str):
        """ alte Spaltenbelegung
        0: Start als Text "dd.mm.yyy-hh:mm"
        1: Ende als Text "dd.mm.yyy-hh:mm"
        2: Reichweite in km
        3: Energie in kWh
        4: durchschnittliche Leistung in W
        5: Dauer als Text "xx H yy Min"
        6: Ladepunktnummer
        7: Lademodus als Zahl
        8: ID-Tag
        9: Kosten
        """
        def conv_1_9_datetimes(datetime_str):
            """ konvertiert Datum-Uhrzeit
                alt: %d.%m.%y-%H:%M 05.03.21-11:16
                neu: %m/%d/%Y, %H:%M:%S 08/04/2021, 15:50:00
            """
            str_date = datetime.datetime.strptime(datetime_str, '%d.%m.%y-%H:%M')
            return datetime.datetime.strftime(str_date, "%m/%d/%Y, %H:%M:%S")

        entries = []
        with open(f"{self.BACKUP_DATA_PATH}/ladelog/{file}") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                try:
                    if len(row) != 0:
                        # Lademodus anpassen
                        if row[7] == "0":
                            chargemode = "instant_charging"
                        elif row[7] == "1" or row[7] == "2":
                            chargemode = "pv_charging"
                        elif row[7] == "3":
                            chargemode = "stop"
                        elif row[7] == "4":
                            chargemode = "standby"
                        elif row[7] == "7":
                            chargemode = "scheduled_charging"
                        else:
                            raise ValueError(
                                str(row[7])+" ist kein bekannter Lademodus.")
                        # Format Datum-Uhrzeit anpassen
                        begin = conv_1_9_datetimes(row[0])
                        end = conv_1_9_datetimes(row[1])
                        # Dauer neu berechnen, da die Dauer unter 1.9 falsch ausgegeben sein kann
                        duration = convert_timedelta_to_time_string(
                            datetime.timedelta(seconds=get_difference(begin, end)))
                        old_cp = row[6].strip()  # sometimes we have trailing spaces
                        if data.data.cp_data.get(f"cp{self.map_to_new_ids(f'cp{old_cp}')}") is not None:
                            cp_name = data.data.cp_data[f"cp{self.map_to_new_ids(f'cp{old_cp}')}"].data.config.name
                        else:
                            cp_name = None
                        rfid = row[8]
                        vehicle_id = ev.get_ev_to_rfid(rfid)
                        if vehicle_id is not None:
                            vehicle_name = data.data.ev_data[f"ev{vehicle_id}"].data.name
                        else:
                            if int(old_cp) == 1 or int(old_cp) == 2:
                                vehicle_id = self.map_to_new_ids(f"ev{old_cp}")
                                vehicle_name = data.data.ev_data[f"ev{vehicle_id}"].data.name
                            else:
                                vehicle_name = None
                        new_entry = {
                            "chargepoint":
                            {
                                "id": self.map_to_new_ids(f"cp{old_cp}"),
                                "name": cp_name,
                            },
                            "vehicle":
                            {
                                "id": vehicle_id,
                                "name": vehicle_name,
                                "chargemode": chargemode,
                                "prio": False,
                                "rfid": rfid
                            },
                            "time":
                            {
                                "begin": begin,
                                "end": end,
                                "time_charged": duration
                            },
                            "data":
                            {
                                "range_charged": float(row[2]),
                                "imported_since_mode_switch": float(row[3]) * 1000,
                                "imported_since_plugged": 0,
                                "power": float(row[4]),
                                "costs": float(row[9])
                            }
                        }
                        entries.append(new_entry)
                except Exception:
                    log.exception(f"Fehler beim Konvertieren des Lade-Logs vom {file}, Reihe {row}")
        return entries

    def convert_csv_to_json_measurement_log(self, folder: str) -> List[Thread]:
        """ konvertiert die alten Tages- und Monats-Log-Dateien in das neue Format für 2.x.
        """
        def convert(old_file_name: str) -> None:
            try:
                if folder == "daily":
                    new_entries = self._daily_log_entry(old_file_name)
                else:
                    new_entries = self._monthly_log_entry(old_file_name)

                pathlib.Path(f'./data/{folder}_log').mkdir(mode=0o755,
                                                           parents=True, exist_ok=True)
                filepath = f"./data/{folder}_log/"+old_file_name[:-4]+".json"
                try:
                    with open(filepath, "r") as jsonFile:
                        content = json.load(jsonFile)
                except FileNotFoundError:
                    write_and_check(filepath, {"entries": [], "totals": {}})
                    with open(filepath, "r") as jsonFile:
                        content = json.load(jsonFile)
                entries = content["entries"]
                merger = self.merge_list_of_records('date')
                merged_entries = merger(new_entries + entries)
                content["totals"] = get_totals(merged_entries)
                content["entries"] = merged_entries
                content["names"] = get_names(content["totals"], LegacySmartHomeLogData().sh_names)
                write_and_check(filepath, content)
            except Exception:
                log.exception(f"Fehler beim Konvertieren des Logs vom {old_file_name}")

        threads: List[Thread] = []
        for old_file_name in os.listdir(f"{self.BACKUP_DATA_PATH}/{folder}"):
            # limit valid files to pattern "YYYYMMDD.csv"
            if folder == "daily":
                filename_pattern = r"\d{8}\.csv$"
            else:
                filename_pattern = r"\d{6}\.csv$"
            if re.match(filename_pattern, old_file_name):
                threads.append(Thread(target=convert, args=[old_file_name, ], name=f"convert {folder} {old_file_name}"))
        return threads

    def _daily_log_entry(self, file: str):
        """ Generator-Funktion, die einen Eintrag aus dem Tages-Log konvertiert.
        alte Spaltenbelegung:
            8, 15, 23 oder 39 Felder! Wurde in 1.9 nie vereinheitlicht!
        Allgemein:
            0: Datum "HHMM"
        EVU:
            1-2: Bezug, Einspeisung
        PV:
            3: PV Gesamt
        LP:
            4-6: LP1, LP2, LP3
            7: Gesamt
            15-19: LP4, LP5, LP6, LP7, LP8
            21-22: SoC LP1, SoC LP2
        Speicher:
            8-9: Ladung, Entladung
            20: SoC
        Verbraucher:
            10-14: VB1 Import, VB1 Export, VB2 Import, VB2 Export, VB3 Import
        SmartHome 2.0:
            23-25: Gerät1 Temp1, Gerät2 Temp2, Gerät1 Temp3
            26-35: Gerät1, Gerät2, Gerät3, Gerät4, Gerät5, Gerät6, Gerät7, Gerät8, Gerät9, Gerät10
            36-38: Gerät2 Temp1, Gerät2 Temp2, Gerät2 Temp3
        """
        DAILY_LOG_CP_ROW_IDS = [4, 5, 6, 15, 16, 17, 18, 19]
        DAILY_LOG_EV_ROW_IDS = [21, 22]
        DAILY_LOG_SH_TEMP_ROW_IDS = [(26, 23, 24, 25), (27, 36, 37, 38)]  # Geräte 1-2 mit Temperaturen 1-3
        DAILY_LOG_SH_ROW_IDS = [28, 29, 30, 31, 32, 33, 34, 35]  # Geräte 3-10
        DAILY_LOG_CONSUMER_ROW_IDS = [(10, 11), (12, 13), (14, None)]

        entries = []
        with open(f"{self.BACKUP_DATA_PATH}/daily/{file}") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                try:
                    if len(row) != 0:
                        time = row[0][:2]+":"+row[0][-2:]
                        new_entry: Dict = {
                            "timestamp": datetime.datetime.strptime(f"{file[:-4]} {time}", "%Y%m%d %H:%M").timestamp(),
                            "date": time,
                            "cp": {},
                            "ev": {},
                            "counter": {},
                            "pv": {},
                            "bat": {},
                            "sh": {},
                            "hc": {}
                        }
                        cp_detail_entry = False
                        for i in range(0, len(DAILY_LOG_CP_ROW_IDS)):
                            if len(row) > DAILY_LOG_CP_ROW_IDS[i]:
                                new_entry_id = self.map_to_new_ids(f"cp{i+1}")
                                if new_entry_id is not None:
                                    cp_detail_entry = True
                                    new_entry["cp"].update(
                                        {f"cp{new_entry_id}": {
                                            "imported": string_to_float(row[DAILY_LOG_CP_ROW_IDS[i]]),
                                            "exported": 0
                                        }})
                        if cp_detail_entry:
                            new_entry["cp"].update({"all": {"imported": string_to_float(row[7]), }})
                        for i in range(0, len(DAILY_LOG_EV_ROW_IDS)):
                            if len(row) > DAILY_LOG_EV_ROW_IDS[i]:
                                new_entry_id = self.map_to_new_ids(f"ev{i+1}")
                                if new_entry_id is not None:
                                    new_entry["ev"].update(
                                        {f"ev{new_entry_id}": {
                                            "soc": string_to_int(row[DAILY_LOG_EV_ROW_IDS[i]])
                                        }})
                        if self.id_map.evu is not None:
                            new_entry["counter"].update({f"counter{self.map_to_new_ids('evu')}": {
                                "imported": string_to_float(row[1]),
                                "exported": string_to_float(row[2])
                            }})
                        if self.id_map.pvAll is not None:
                            new_entry["pv"].update(
                                {"all": {"exported": string_to_float(row[3])},
                                 f"pv{self.map_to_new_ids('pvAll')}": {
                                    "exported": string_to_float(row[3])}}
                            )
                        if self.id_map.bat is not None:
                            new_entry["bat"].update({"all": {
                                "imported": string_to_float(row[8]) if len(row) >= 9 else 0,
                                "exported": string_to_float(row[9]) if len(row) >= 10 else 0,
                                "soc": string_to_int(row[20]) if len(row) >= 23 else 0
                            }, f"bat{self.map_to_new_ids('bat')}": {
                                "imported": string_to_float(row[8]) if len(row) >= 9 else 0,
                                "exported": string_to_float(row[9]) if len(row) >= 10 else 0,
                                "soc": string_to_int(row[20]) if len(row) >= 23 else 0
                            }})
                        # SmartHome Devices 1+2 with temperatures
                        for i in range(0, len(DAILY_LOG_SH_TEMP_ROW_IDS)):
                            if len(row) > DAILY_LOG_SH_TEMP_ROW_IDS[i][0]:
                                new_entry_id = self.map_to_new_ids(f"sh{i+1}")
                                if new_entry_id is not None:
                                    new_entry["sh"].update(
                                        {f"sh{new_entry_id}": {
                                            "imported": string_to_float(row[DAILY_LOG_SH_TEMP_ROW_IDS[i][0]]),
                                            "temp0": string_to_float(row[DAILY_LOG_SH_TEMP_ROW_IDS[i][1]]),
                                            "temp1": string_to_float(row[DAILY_LOG_SH_TEMP_ROW_IDS[i][2]]),
                                            "temp2": string_to_float(row[DAILY_LOG_SH_TEMP_ROW_IDS[i][3]]),
                                            "exported": 0
                                        }})
                        # SmartHome 2.0 Devices 3-10 without temperatures
                        for i in range(0, len(DAILY_LOG_SH_ROW_IDS)):
                            if len(row) > DAILY_LOG_SH_ROW_IDS[i]:
                                new_entry_id = self.map_to_new_ids(f"sh{i+3}")  # we start with device 3!
                                if new_entry_id is not None:
                                    new_entry["sh"].update(
                                        {f"sh{new_entry_id}": {
                                            "imported": string_to_float(row[DAILY_LOG_SH_ROW_IDS[i]]),
                                            "exported": 0
                                        }})
                        # old SmartHome "Verbraucher"
                        for i in range(0, len(DAILY_LOG_CONSUMER_ROW_IDS)):
                            if len(row) > DAILY_LOG_CONSUMER_ROW_IDS[i][0]:
                                new_entry_id = self.map_to_new_ids(f"consumer{i+1}")
                                if new_entry_id is not None:
                                    new_entry["counter"].update(
                                        {f"counter{new_entry_id}": {
                                            "imported": string_to_float(row[DAILY_LOG_CONSUMER_ROW_IDS[i][0]]),
                                            "exported": string_to_float(row[
                                                DAILY_LOG_CONSUMER_ROW_IDS[i][1]
                                            ]) if DAILY_LOG_CONSUMER_ROW_IDS[i][1] is not None else 0
                                        }})
                        entries.append(new_entry)
                except Exception:
                    log.exception(f"Fehler beim Konvertieren des Tages-Logs vom {file}, Reihe {row}")
        return entries

    def _monthly_log_entry(self, file: str):
        """ Generator-Funktion, die einen Eintrag aus dem Tages-Log konvertiert.
        alte Spaltenbelegung:
            12, 19 oder 29 Felder! Wurde in 1.9 nicht vereinheitlicht!
        Allgemein:
            0: Datum "YYYMMDD"
        EVU:
            1-2: Bezug, Einspeisung
        PV:
            3: PV Gesamt
        LP:
            4-6: LP1, LP2, LP3
            7: Gesamt
            12-16: LP4, LP5, LP6, LP7, LP8
        Verbraucher:
            8-11: VB1 Import, VB1 Export, VB2 Import, VB2 Export
        Speicher:
            17-18: Ladung, Entladung
        SmartHome 2.0:
            19-28: Gerät1, Gerät2, Gerät3, Gerät4, Gerät5, Gerät6, Gerät7, Gerät8, Gerät9, Gerät10
        """
        MONTHLY_LOG_CP_ROW_IDS = [4, 5, 6, 12, 13, 14, 15, 16]
        MONTHLY_LOG_SH_ROW_IDS = [19, 20, 21, 22, 23, 24, 25, 26, 27, 28]
        MONTHLY_LOG_CONSUMER_ROW_IDS = [(8, 9), (10, 11)]

        entries = []
        with open(f"{self.BACKUP_DATA_PATH}/monthly/{file}") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                try:
                    if len(row) != 0:
                        new_entry: Dict = {
                            "timestamp": datetime.datetime.strptime(f"{row[0]}", "%Y%m%d").timestamp(),
                            "date": row[0],
                            "cp": {},
                            "ev": {},
                            "counter": {},
                            "pv": {},
                            "bat": {},
                            "sh": {},
                            "hc": {}
                        }
                        cp_detail_entry = False
                        for i in range(0, len(MONTHLY_LOG_CP_ROW_IDS)):
                            if len(row) > MONTHLY_LOG_CP_ROW_IDS[i]:
                                new_entry_id = self.map_to_new_ids(f"cp{i+1}")
                                if new_entry_id is not None:
                                    cp_detail_entry = True
                                    new_entry["cp"].update(
                                        {f"cp{new_entry_id}": {
                                            "imported": string_to_float(row[MONTHLY_LOG_CP_ROW_IDS[i]]),
                                            "exported": 0
                                        }})
                        if cp_detail_entry:
                            new_entry["cp"].update({"all": {"imported": string_to_float(row[7]), }})
                        if self.id_map.evu is not None:
                            new_entry["counter"].update({f"counter{self.map_to_new_ids('evu')}": {
                                "imported": string_to_float(row[1]),
                                "exported": string_to_float(row[2])
                            }})
                        if self.id_map.pvAll is not None:
                            new_entry["pv"].update(
                                {"all": {"exported": string_to_float(row[3])},
                                 f"pv{self.map_to_new_ids('pvAll')}": {"exported": string_to_float(row[3])}})
                        if self.id_map.bat is not None:
                            if len(row) >= 19:
                                new_entry["bat"].update({
                                    "all": {
                                        "imported": string_to_float(row[17]),
                                        "exported": string_to_float(row[18]),
                                    },
                                    f"bat{self.map_to_new_ids('bat')}": {
                                        "imported": string_to_float(row[17]),
                                        "exported": string_to_float(row[18]),
                                    }
                                })
                        for i in range(0, len(MONTHLY_LOG_SH_ROW_IDS)):
                            if len(row) > MONTHLY_LOG_SH_ROW_IDS[i]:
                                new_entry_id = self.map_to_new_ids(f"sh{i+1}")
                                if new_entry_id is not None:
                                    new_entry["sh"].update(
                                        {f"sh{new_entry_id}": {
                                            "imported": string_to_float(row[MONTHLY_LOG_SH_ROW_IDS[i]]),
                                            "exported": 0
                                        }})
                        for i in range(0, len(MONTHLY_LOG_CONSUMER_ROW_IDS)):
                            if len(row) > MONTHLY_LOG_CONSUMER_ROW_IDS[i][1]:
                                new_entry_id = self.map_to_new_ids(f"consumer{i+1}")
                                if new_entry_id is not None:
                                    new_entry["counter"].update(
                                        {f"counter{new_entry_id}": {
                                            "imported": string_to_float(row[MONTHLY_LOG_CONSUMER_ROW_IDS[i][0]]),
                                            "exported": string_to_float(row[MONTHLY_LOG_CONSUMER_ROW_IDS[i][1]])
                                        }})
                        entries.append(new_entry)
                except Exception:
                    log.exception(f"Fehler beim Konvertieren des Monats-Logs vom {file}, Reihe {row}")
        return entries

    def _get_openwb_conf_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        value = default
        found = False
        for line in self.openwb_conf:
            if key in line:
                raw_value = line.replace(f"{key}=", "")
                value = raw_value.rstrip("\n")
                found = True
                break
        if not found:
            log.debug(f"Keine Konfiguration für '{key}' gefunden. Verwende Standardwert '{default}'.")
        return value

    def _migrate_settings_from_openwb_conf(self):
        with open("./data/data_migration/var/www/html/openWB/openwb.conf", "r") as file:
            self.openwb_conf = file.readlines()
        self._move_serial_number()
        self._move_cloud_data()
        self._move_rse()
        self._move_max_c_socket()
        self._move_pddate()

    def _move_serial_number(self) -> None:
        serial_number = self._get_openwb_conf_value("snnumber")
        if serial_number is not None:
            write_and_check("/home/openwb/snnumber", f"snnumber={serial_number}")

    def _move_cloud_data(self) -> None:
        cloud_user = self._get_openwb_conf_value("clouduser")
        cloud_pw = self._get_openwb_conf_value("cloudpw")
        if cloud_user is not None and cloud_pw is not None:
            Pub().pub("openWB/set/command/data_migration/todo",
                      {"command": "connectCloud", "data": {"username": cloud_user, "password": cloud_pw, "partner": 0}})

    def _move_rse(self) -> None:
        if bool(self._get_openwb_conf_value("rseenabled", "0")):
            Pub().pub("openWB/set/general/ripple_control_receiver/module", dataclass_utils.asdict(GpioRcr()))

    def _move_max_c_socket(self):
        try:
            max_c_socket = int(self._get_openwb_conf_value("ppbuchse", "32"))
            update_hardware_configuration({"max_c_socket": max_c_socket})
        except TypeError:
            log.warning("Keine Konfiguration für die Buchse in den zu portierenden Daten gefunden.")

    def _move_pddate(self) -> None:
        pddate = self._get_openwb_conf_value("pddate")
        if pddate is not None:
            write_and_check("/home/openwb/pddate", f"pddate={pddate}")

    NOT_CONFIGURED = " wurde in openWB software2 nicht konfiguriert."

    def validate_ids(self) -> None:
        for key, id in asdict(self.id_map).items():
            if id is not None:
                if "cp" in key:
                    if data.data.cp_data.get(f"cp{id}") is None:
                        raise ValueError(f"Die Ladepunkt-ID {id}{self.NOT_CONFIGURED}")
                elif "evu" in key or "consumer" in key:
                    if data.data.counter_data.get(f"counter{id}") is None:
                        raise ValueError(f"Die Zähler-ID {id}{self.NOT_CONFIGURED}")
                elif "pv" in key:
                    if data.data.pv_data.get(f"pv{id}") is None:
                        raise ValueError(f"Die Wechselrichter-ID {id}{self.NOT_CONFIGURED}")
                elif "bat" in key:
                    if data.data.bat_data.get(f"bat{id}") is None:
                        raise ValueError(f"Die Speicher-ID {id}{self.NOT_CONFIGURED}")

    def _merge_records_by(self, key):
        """Returns a function that merges two records rec_a and rec_b.
        The records are assumed to have the same value for rec_a[key]
        and rec_b[key].
        """
        return lambda rec_a, rec_b: {
            k: rec_a[k] if k == key else rec_a[k]
            for k in rec_a
        }

    def merge_list_of_records(self, key):
        """https://codereview.stackexchange.com/a/85822
        Returns a function that merges a list of records, grouped by
        the specified key, with values combined using the specified
        binary operator."""
        key_prop = itemgetter(key)
        return lambda lst: [
            reduce(self._merge_records_by(key), records)
            for _, records in groupby(sorted(lst, key=key_prop), key_prop)
        ]
