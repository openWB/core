""" Konvertierungsmodul von 1.9x nach 2.x
Konvertiert die Lade- und Tageslog-Dateien von csv nach json.
Falls nötig, ohne Abhängigkeit zur sonstigen 2.x-Implementierung.
"""

import csv
import datetime
import json
import logging
import os
import pathlib
import shutil
import tarfile
from typing import Callable, Dict, Union


from dataclass_utils import dataclass_from_dict
from helpermodules.conv_1_9.id_mapping import MapId
from helpermodules.measurement_log import get_totals

try:
    from .control import data
except Exception:
    pass

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


class Conversion:
    BACKUP_DATA_PATH = "./data/backup/conversion/var/www/html/openWB/web/logging/data"

    def __init__(self, id_map: Dict, backup_name: str) -> None:
        self.id_map = dataclass_from_dict(MapId, id_map)
        self.backup_name = backup_name

    def convert(self):
        self.extract_files("ladelog")
        self.extract_files("daily")
        self.extract_files("monthly")
        self.convert_csv_to_json_chargelog()
        self.convert_csv_to_json_measurement_log("daily")
        self.convert_csv_to_json_measurement_log("monthly")
        # shutil.rmtree("./data/backup/conversion")

    def map_to_new_ids(self, old_id: str) -> int:
        return getattr(self.id_map, old_id)

    def _file_to_extract_generator(self, members, log_folder_name: str):
        for tarinfo in members:
            if tarinfo.name.startswith(f"var/www/html/openWB/web/logging/data/{log_folder_name}"):
                yield tarinfo

    def extract_files(self, log_folder_name: str):
        with tarfile.open(f'./data/backup/conversion/{self.backup_name}') as tar:
            tar.extractall(members=self._file_to_extract_generator(
                tar, log_folder_name), path="./data/backup/conversion")

    def convert_csv_to_json_chargelog(self):
        """ konvertiert die alten Ladelog-Dateien in das neue Format für 2.x.
        """
        for old_file_name in os.listdir(f"{self.BACKUP_DATA_PATH}/ladelog"):
            try:
                new_entries = self._chargelogfile_entries(old_file_name)

                pathlib.Path('./charge_log').mkdir(mode=0o755,
                                                   parents=True, exist_ok=True)
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

    def _chargelogfile_entries(self, file: str):
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
                        try:
                            costs = data.data.general_data.data.price_kwh * row[3]
                        except Exception:
                            costs = 0
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
                                "imported_since_mode_switch": 0,
                                "imported_since_plugged": float(row[3]),
                                "power": float(row[4]),
                                "costs": get_rounding_function_by_digits(2)(costs)
                            }
                        }
                        entries.append(new_entry)
                except Exception:
                    log.exception(f"Fehler beim Konvertieren des Ladelogs vom {file}, Reihe {row}")
        return entries

    def convert_csv_to_json_measurement_log(self, folder: str):
        """ konvertiert die alten Tages- und Monatslog-Dateien in das neue Format für 2.x.
        """
        for old_file_name in os.listdir(f"{self.BACKUP_DATA_PATH}/{folder}"):
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
                new_entries.extend(entries)
                content["totals"] = get_totals(new_entries)
                content["entries"] = new_entries

                with open(filepath, "w") as jsonFile:
                    json.dump(content, jsonFile)
            except Exception:
                log.exception(f"Fehler beim Konvertieren des Logogs vom {old_file_name}")

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
                        new_entry: Dict = {
                            "date": row[0][:2]+":"+row[0][-2:],
                            "cp": {},
                            "ev": {},
                            "counter": {},
                            "pv": {},
                            "bat": {},
                            "sh": {}
                        }
                        new_entry["cp"].update({"all": {"imported": row[7], }})
                        for i in range(1, 9):
                            new_entry_id = self.map_to_new_ids(f"cp{i}")
                            if new_entry_id is not None:
                                new_entry["cp"].update(
                                    {f"cp{new_entry_id}": {"imported": row[self.DAILY_LOG_CP_ROW_IDS[i - 1]],
                                                           "exported": 0}})
                        for i in range(1, 2):
                            new_entry_id = self.map_to_new_ids(f"ev{i}")
                            if new_entry_id is not None:
                                new_entry["ev"].update(
                                    {f"ev{new_entry_id}": {"soc": row[self.DAILY_LOG_EV_ROW_IDS[i - 1]]}})
                        new_entry["counter"].update({f"counter{self.map_to_new_ids('evu')}": {
                            "imported": row[1],
                            "exported": row[2]
                        }})
                        new_entry["pv"].update({"all": {"imported": row[3]}})
                        new_entry["bat"].update({"all": {
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
                        for i in range(1, 2):
                            new_entry_id = self.map_to_new_ids(f"consumer{i}")
                            if new_entry_id is not None:
                                new_entry["sh"].update(
                                    {f"consumer{new_entry_id}": {
                                        "imported": row[self.DAILY_LOG_CONSUMER_ROW_IDS[i - 1][0]],
                                        "exported": row[self.DAILY_LOG_CONSUMER_ROW_IDS[i - 1][1]]
                                    }})
                        new_entry["sh"].update({"consumer3": {"imported": row[14]}})
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
                            "date": row[0],
                            "cp": {},
                            "ev": {},
                            "counter": {},
                            "pv": {},
                            "bat": {},
                            "sh": {}
                        }
                        new_entry["cp"].update({"all": {"imported": row[7], }})
                        for i in range(1, 9):
                            new_entry_id = self.map_to_new_ids(f"cp{i}")
                            if new_entry_id is not None:
                                new_entry["cp"].update(
                                    {f"cp{new_entry_id}": {"imported": row[self.MONTHLY_LOG_CP_ROW_IDS[i - 1]],
                                                           "exported": 0}})
                        new_entry["counter"].update({f"counter{self.map_to_new_ids('evu')}": {
                            "imported": row[1],
                            "exported": row[2]
                        }})
                        new_entry["pv"].update({"all": {"imported": row[3]}})
                        new_entry["bat"].update({"all": {
                            "imported": row[17],
                            "exported": row[18],
                        }})
                        for i in range(1, 11):
                            new_entry_id = self.map_to_new_ids(f"sh{i}")
                            if new_entry_id is not None:
                                new_entry["sh"].update(
                                    {f"sh{new_entry_id}": {
                                        "imported": row[18 + i],  # Row starts at 19 for device 1
                                        "exported": 0
                                    }})
                        for i in range(1, 2):
                            new_entry_id = self.map_to_new_ids(f"consumer{i}")
                            if new_entry_id is not None:
                                new_entry["sh"].update(
                                    {f"consumer{new_entry_id}": {
                                        "imported": row[self.MONTHLY_LOG_CONSUMER_ROW_IDS[i - 1][0]],
                                        "exported": row[self.MONTHLY_LOG_CONSUMER_ROW_IDS[i - 1][1]]
                                    }})
                        entries.append(new_entry)
                except Exception:
                    log.exception(f"Fehler beim Konvertieren des Monatslogs vom {file}, Reihe {row}")
        return entries


Conversion(MapId(), "openWB_backup_2023-07-06_16-28-57.tar.gz").convert()
