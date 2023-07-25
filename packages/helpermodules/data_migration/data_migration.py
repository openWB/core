""" Konvertierungsmodul von 1.9x nach software2
Konvertiert die Lade- und Tageslog-Dateien von csv nach json.
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
from typing import Callable, Dict, List, Union

from control import data
from dataclass_utils import dataclass_from_dict
from helpermodules.data_migration.id_mapping import MapId
from helpermodules.measurement_log import LegacySmarthomeLogdata, get_names, get_totals
from helpermodules.utils import thread_handler
from helpermodules.pub import Pub

log = logging.getLogger(__name__)


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
    BACKUP_DATA_PATH = "./data/data_migration/var/www/html/openWB/web/logging/data"

    def __init__(self, id_map: Dict) -> None:
        self.id_map = dataclass_from_dict(MapId, id_map)

    def migrate(self):
        self.extract_files("ladelog")
        self.extract_files("daily")
        self.extract_files("monthly")
        thread_handler(self.convert_csv_to_json_chargelog(), None)
        thread_handler(self.convert_csv_to_json_measurement_log("daily"), None)
        thread_handler(self.convert_csv_to_json_measurement_log("monthly"), None)
        self.move_serial_number_clouddata()
        shutil.rmtree("./data/data_migration/var")
        os.remove("./data/data_migration/data_migration.tar.gz")

    def map_to_new_ids(self, old_id: str) -> int:
        return getattr(self.id_map, old_id)

    def _file_to_extract_generator(self, members, log_folder_name: str):
        for tarinfo in members:
            if tarinfo.name.startswith(f"var/www/html/openWB/web/logging/data/{log_folder_name}"):
                yield tarinfo

    def extract_files(self, log_folder_name: str):
        with tarfile.open('./data/data_migration/data_migration.tar.gz') as tar:
            tar.extractall(members=self._file_to_extract_generator(
                tar, log_folder_name), path="./data/data_migration")

    def convert_csv_to_json_chargelog(self) -> List[Thread]:
        """ konvertiert die alten Ladelog-Dateien in das neue Format für 2.x.
        """
        def convert(old_file_name: str) -> None:
            try:
                new_entries = self._chargelogfile_entries(old_file_name)

                pathlib.Path('./data/charge_log').mkdir(mode=0o755, parents=True, exist_ok=True)
                filepath = f"./data/charge_log/{old_file_name[:-4]}.json"
                try:
                    with open(filepath, "r") as jsonFile:
                        content = json.load(jsonFile)
                except FileNotFoundError:
                    with open(filepath, "w+") as jsonFile:
                        json.dump([], jsonFile)
                    with open(filepath, "r") as jsonFile:
                        content = json.load(jsonFile)
                new_entries.extend(content)
                with open(filepath, "w") as jsonFile:
                    json.dump(new_entries, jsonFile)
            except Exception:
                log.exception(f"Fehler beim Konvertieren des Ladelogs vom {old_file_name}")

        threads: List[Thread] = []
        for old_file_name in os.listdir(f"{self.BACKUP_DATA_PATH}/ladelog"):
            threads.append(Thread(target=convert, args=[old_file_name, ], name=f"chargelog {old_file_name}"))
        return threads

    def _chargelogfile_entries(self, file: str):
        """ alte Spaltenbelegung
        $start,$jetzt,$gelr,$bishergeladen,$ladegeschw,$ladedauertext,$chargePointNumber,$lademoduslogvalue,$rfid,$kosten
        """
        def conv_1_9_datetimes(datetime_str):
            """ konvertiert Datum-Uhrzeit alt: %d.%m.%y-%H:%M 05.03.21-11:16; neu: %m/%d/%Y, %H:%M 08/04/2021, 15:50
            """
            str_date = datetime.datetime.strptime(datetime_str, '%d.%m.%y-%H:%M')
            return datetime.datetime.strftime(str_date, "%m/%d/%Y, %H:%M")

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
                        # Dauer formatieren
                        duration_list = row[5].split(" ")
                        if len(duration_list) == 2:
                            duration_list.pop(1)  # "Min"
                            duration = duration_list[0] + ":00"
                        elif len(duration_list) == 4:
                            duration_list.pop(1)  # "H"
                            duration_list.pop(2)  # "Min"
                            duration = duration_list[0] + \
                                ":" + duration_list[1] + ":00"
                        else:
                            raise ValueError(str(duration_list) +
                                             " hat kein bekanntes Format.")
                        new_entry = {
                            "chargepoint":
                            {
                                "id": int(row[6]),
                                "name": "-",
                            },
                            "vehicle":
                            {
                                "id": "-",
                                "name": "-",
                                "chargemode": chargemode,
                                "prio": "-",
                                "rfid": row[8]
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
                    log.exception(f"Fehler beim Konvertieren des Ladelogs vom {file}, Reihe {row}")
        return entries

    def convert_csv_to_json_measurement_log(self, folder: str) -> List[Thread]:
        """ konvertiert die alten Tages- und Monatslog-Dateien in das neue Format für 2.x.
        """
        def convert(old_file_name: str) -> None:
            try:
                if folder == "daily":
                    new_entries = self._dailylog_entry(old_file_name)
                else:
                    new_entries = self._monthlylog_entry(old_file_name)

                pathlib.Path(f'./data/{folder}_log').mkdir(mode=0o755,
                                                           parents=True, exist_ok=True)
                filepath = f"./data/{folder}_log/"+old_file_name[:-4]+".json"
                try:
                    with open(filepath, "r") as jsonFile:
                        content = json.load(jsonFile)
                except FileNotFoundError:
                    with open(filepath, "w+") as jsonFile:
                        json.dump({"entries": [], "totals": {}}, jsonFile)
                    with open(filepath, "r") as jsonFile:
                        content = json.load(jsonFile)
                entries = content["entries"]
                merger = self.merge_list_of_records('date')
                merged_entries = merger(new_entries + entries)
                content["totals"] = get_totals(merged_entries)
                content["entries"] = merged_entries
                content["names"] = get_names(content["totals"], LegacySmarthomeLogdata().update()[1])
                with open(filepath, "w") as jsonFile:
                    json.dump(content, jsonFile)
            except Exception:
                log.exception(f"Fehler beim Konvertieren des Logs vom {old_file_name}")

        threads: List[Thread] = []
        for old_file_name in os.listdir(f"{self.BACKUP_DATA_PATH}/{folder}"):
            threads.append(Thread(target=convert, args=[old_file_name, ], name=f"convert {folder} {old_file_name}"))
        return threads

    DAILY_LOG_CP_ROW_IDS = [4, 5, 6, 15, 16, 17, 18, 19]
    DAILY_LOG_EV_ROW_IDS = [21, 22]
    DAILY_LOG_SH_TEMP_ROW_IDS = [(26, 23, 24, 25), (27, 36, 37, 38)]
    DAILY_LOG_SH_ROW_IDS = [(26, 23, 24, 25), (27, 36, 37, 38)]  # Geräte 3-10
    DAILY_LOG_CONSUMER_ROW_IDS = [(10, 11), (12, 13)]

    def _dailylog_entry(self, file: str):
        """ Generator-Funktion, die einen Eintrag aus dem Tageslog konvertiert.
        alte Spaltenbelegung:
        date, $bezug,$einspeisung,$pv,$ll1,$ll2,$ll3,$llg,$speicheri,$speichere,$verbraucher1,$verbrauchere1
        $verbraucher2,
        $verbrauchere2,$verbraucher3,$ll4,$ll5,$ll6,$ll7,$ll8,$speichersoc,$soc,$soc1,$temp1,$temp2,$temp3,$d1,$d2,$d3,$d4,
        $d5,$d6,$d7,$d8,$d9,$d10,$temp4,$temp5,$temp6
        """
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
                            "sh": {}
                        }
                        cp_detail_entry = False
                        for i in range(1, 9):
                            new_entry_id = self.map_to_new_ids(f"cp{i}")
                            if new_entry_id is not None:
                                cp_detail_entry = True
                                new_entry["cp"].update(
                                    {f"cp{new_entry_id}": {"imported": row[self.DAILY_LOG_CP_ROW_IDS[i - 1]],
                                                           "exported": 0}})
                        if cp_detail_entry:
                            new_entry["cp"].update({"all": {"imported": row[7], }})
                        for i in range(1, 3):
                            new_entry_id = self.map_to_new_ids(f"ev{i}")
                            if new_entry_id is not None:
                                new_entry["ev"].update(
                                    {f"ev{new_entry_id}": {"soc": row[self.DAILY_LOG_EV_ROW_IDS[i - 1]]}})
                        if self.id_map.evu is not None:
                            new_entry["counter"].update({f"counter{self.map_to_new_ids('evu')}": {
                                "imported": row[1],
                                "exported": row[2]
                            }})
                        if self.id_map.pvAll is not None:
                            new_entry["pv"].update({"all": {"exported": row[3]},
                                                    f"pv{self.map_to_new_ids('pvAll')}": {"exported": row[3]}})
                        if self.id_map.bat is not None:
                            new_entry["bat"].update({"all": {
                                "imported": row[8],
                                "exported": row[9],
                                "soc": row[20]
                            }, f"bat{self.map_to_new_ids('bat')}": {
                                "imported": row[8],
                                "exported": row[9],
                                "soc": row[20]
                            }})
                        for i in range(1, 3):
                            new_entry_id = self.map_to_new_ids(f"sh{i}")
                            if new_entry_id is not None:
                                new_entry["sh"].update(
                                    {f"sh{new_entry_id}": {
                                        "imported": row[self.DAILY_LOG_SH_TEMP_ROW_IDS[i - 1][0]],
                                        "temp0": row[self.DAILY_LOG_SH_TEMP_ROW_IDS[i - 1][1]],
                                        "temp1": row[self.DAILY_LOG_SH_TEMP_ROW_IDS[i - 1][2]],
                                        "temp2": row[self.DAILY_LOG_SH_TEMP_ROW_IDS[i - 1][3]],
                                        "exported": 0
                                    }})
                        for i in range(3, 11):
                            new_entry_id = self.map_to_new_ids(f"sh{i}")
                            if new_entry_id is not None:
                                new_entry["sh"].update(
                                    {f"sh{new_entry_id}": {
                                        "imported": row[25 + i],  # Row starts at 28 for device 3
                                        "exported": 0
                                    }})
                        for i in range(1, 3):
                            new_entry_id = self.map_to_new_ids(f"consumer{i}")
                            if new_entry_id is not None:
                                new_entry["counter"].update(
                                    {f"counter{new_entry_id}": {
                                        "imported": row[self.DAILY_LOG_CONSUMER_ROW_IDS[i - 1][0]],
                                        "exported": row[self.DAILY_LOG_CONSUMER_ROW_IDS[i - 1][1]]
                                    }})
                        if self.id_map.consumer3 is not None:
                            new_entry["counter"].update({f"counter{self.map_to_new_ids('consumer3')}":
                                                        {"imported": row[14], "exported": 0}})
                        entries.append(new_entry)
                except Exception:
                    log.exception(f"Fehler beim Konvertieren des Tageslogs vom {file}, Reihe {row}")
        return entries

    MONTHLY_LOG_CP_ROW_IDS = [4, 5, 6, 12, 13, 14, 15, 16]
    MONTHLY_LOG_CONSUMER_ROW_IDS = [(8, 9), (10, 11)]

    def _monthlylog_entry(self, file: str):
        """ Generator-Funktion, die einen Eintrag aus dem Tageslog konvertiert.
        alte Spaltenbelegung: date,$bezug,$einspeisung,$pv,$ll1,$ll2,$ll3,$llg,$verbraucher1iwh,$verbraucher1ewh,
        $verbraucher2iwh,$verbraucher2ewh,$ll4,$ll5,$ll6,$ll7,$ll8,$speicherikwh,$speicherekwh,$d1,$d2,$d3,$d4,
        $d5,$d6,$d7,$d8,$d9,$d10
        """
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
                            "sh": {}
                        }
                        cp_detail_entry = False
                        for i in range(1, 9):
                            new_entry_id = self.map_to_new_ids(f"cp{i}")
                            if new_entry_id is not None:
                                cp_detail_entry = True
                                new_entry["cp"].update(
                                    {f"cp{new_entry_id}": {"imported": row[self.MONTHLY_LOG_CP_ROW_IDS[i - 1]],
                                                           "exported": 0}})
                        if cp_detail_entry:
                            new_entry["cp"].update({"all": {"imported": row[7], }})
                        if self.id_map.evu is not None:
                            new_entry["counter"].update({f"counter{self.map_to_new_ids('evu')}": {
                                "imported": row[1],
                                "exported": row[2]
                            }})
                        if self.id_map.pvAll is not None:
                            new_entry["pv"].update({"all": {"exported": row[3]},
                                                    f"pv{self.map_to_new_ids('pvAll')}": {"exported": row[3]}})
                        if self.id_map.bat is not None:
                            new_entry["bat"].update({
                                "all": {
                                    "imported": row[17],
                                    "exported": row[18],
                                },
                                f"bat{self.map_to_new_ids('bat')}": {
                                    "imported": row[17],
                                    "exported": row[18],
                                }
                            })
                        for i in range(1, 11):
                            new_entry_id = self.map_to_new_ids(f"sh{i}")
                            if new_entry_id is not None:
                                new_entry["sh"].update(
                                    {f"sh{new_entry_id}": {
                                        "imported": row[18 + i],  # Row starts at 19 for device 1
                                        "exported": 0
                                    }})
                        for i in range(1, 3):
                            new_entry_id = self.map_to_new_ids(f"consumer{i}")
                            if new_entry_id is not None:
                                new_entry["counter"].update(
                                    {f"counter{new_entry_id}": {
                                        "imported": row[self.MONTHLY_LOG_CONSUMER_ROW_IDS[i - 1][0]],
                                        "exported": row[self.MONTHLY_LOG_CONSUMER_ROW_IDS[i - 1][1]]
                                    }})
                        entries.append(new_entry)
                except Exception:
                    log.exception(f"Fehler beim Konvertieren des Monatslogs vom {file}, Reihe {row}")
        return entries

    def move_serial_number_clouddata(self) -> None:
        def strip_openwb_conf_entry(entry: str, key: str) -> str:
            value = entry.replace(f"{key}=", "")
            return value.rstrip("\n")
        with tarfile.open('./data/data_migration/data_migration.tar.gz') as tar:
            tar.extract(member="var/www/html/openWB/openwb.conf", path="./data/data_migration")
        with open("./data/data_migration/var/www/html/openWB/openwb.conf", "r") as file:
            serial_number = ""
            openwb_conf = file.readlines()
            for line in openwb_conf:
                if "snnumber" in line:
                    serial_number = strip_openwb_conf_entry(line, "snnumber")
                    break
            else:
                log.debug("Keine Seriennummer gefunden.")
        with open("/home/openwb/snnumber", "w") as file:
            file.write(f"snnumber={serial_number}")

        with open("./data/data_migration/var/www/html/openWB/openwb.conf", "r") as file:
            clouduser = ""
            cloudpw = ""
            openwb_conf = file.readlines()
            for line in openwb_conf:
                if "clouduser" in line:
                    clouduser = strip_openwb_conf_entry(line, "clouduser")
                elif "cloudpw" in line:
                    cloudpw = strip_openwb_conf_entry(line, "cloudpw")
            if clouduser == "":
                log.debug("Keine Cloudzugangsdaten gefunden.")
        Pub().pub("openWB/set/command/data_migration/todo",
                  {"command": "connectCloud", "data": {"username": clouduser, "password": cloudpw, "partner": 0}})

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
        keyprop = itemgetter(key)
        return lambda lst: [
            reduce(self._merge_records_by(key), records)
            for _, records in groupby(sorted(lst, key=keyprop), keyprop)
        ]
