""" Konvertierungsmodul von 1.9x nach 2.x
Konvertiert die Lade- und Tageslog-Dateien von csv nach json.
Falls nötig, ohne Abhängigkeit zur sonstigen 2.x-Implementierung.
"""

import csv
import datetime
import json
import os
import pathlib
from typing import Dict

try:
    from .. import data
except Exception:
    pass

from modules.common.store._util import get_rounding_function_by_digits


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
    def __init__(self, id_map) -> None:
        self.id_map = id_map

    def map_to_new_ids(self, old_id: str) -> int:
        return getattr(self.id_map, old_id)

    def convert_csv_to_json_chargelog(self):
        """ konvertiert die alten Ladelog-Dateien in das neue Format für 2.x.
        """
        logfiles = os.listdir("/var/www/html/openWB/web/logging/data/ladelog")
        for file in logfiles:
            try:
                pathlib.Path('./data/monthly_log').mkdir(mode=0o755,
                                                         parents=True, exist_ok=True)
                filepath = "./data/monthly_log/"+file[:-4]+".json"
                pathlib.Path(filepath).touch(exist_ok=True)
                with open(filepath, 'w') as f:
                    generator_handle = self._chargelogfile_entry_generator_func(file)
                    stream_array = StreamArray(generator_handle)
                    for entry in json.JSONEncoder().iterencode(stream_array):
                        f.write(entry)
            except Exception:
                pass

    def _chargelogfile_entry_generator_func(self, file: str):
        """ Generator-Funktion, die einen Eintrag aus dem Ladelog konvertiert.
        """

        def conv_1_9_datetimes(datetime_str):
            """ konvertiert Datum-Uhrzeit alt: %d.%m.%y-%H:%M 05.03.21-11:16; neu: %m/%d/%Y, %H:%M 08/04/2021, 15:50
            """
            str_date = datetime.datetime.strptime(datetime_str, '%d.%m.%y-%H:%M')
            return datetime.datetime.strftime(str_date, "%m/%d/%Y, %H:%M")

        with open('/var/www/html/openWB/web/logging/data/ladelog/'+file) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                try:
                    if len(row) != 0:
                        # Lademodus anpassen
                        if row[7] == "0":
                            chargemode = "instant_charging"
                        elif row[7] == "1":
                            chargemode = "pv_charging"
                        elif row[7] == "2":
                            chargemode = "pv_charging"
                        elif row[7] == "3":
                            chargemode = "stop"
                        elif row[7] == "4":
                            chargemode = "standby"
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
                    else:
                        new_entry = {}
                    yield new_entry

                except Exception:
                    pass

    def convert_csv_to_json_measurement_log(self, folder: str):
        """ konvertiert die alten Tages- und Monatslog-Dateien in das neue Format für 2.x.
        """
        logfiles = os.listdir("/var/www/html/openWB/web/logging/data/"+folder)
        for file in logfiles:
            try:
                pathlib.Path('./data/'+folder+'_log').mkdir(mode=0o755,
                                                            parents=True, exist_ok=True)
                filepath = "./data/"+folder+"_log/"+file[:-4]+".json"
                pathlib.Path(filepath).touch(exist_ok=True)
                with open(filepath, 'w') as f:
                    if folder == "daily":
                        generator_handle = self._dailylog_entry_generator_func(file)
                    else:
                        generator_handle = self._monthlylog_entry_generator_func(file)
                    stream_array = StreamArray(generator_handle)
                    for entry in json.JSONEncoder().iterencode(stream_array):
                        f.write(entry)
            except Exception:
                pass

    DAILY_LOG_CP_ROW_IDS = [4, 5, 6, 15, 16, 17, 18, 19]
    DAILY_LOG_EV_ROW_IDS = [21, 22]
    DAILY_LOG_SH_TEMP_ROW_IDS = [(26, 23, 24, 25), (27, 36, 37, 38)]
    DAILY_LOG_SH_ROW_IDS = [(26, 23, 24, 25), (27, 36, 37, 38)]  # Geräte 3-10
    DAILY_LOG_CONSUMER_ROW_IDS = [(10, 11), (12, 13)]

    def _dailylog_entry_generator_func(self, file: str):
        """ Generator-Funktion, die einen Eintrag aus dem Tageslog konvertiert.
        alte Spaltenbelegung:
        date, $bezug,$einspeisung,$pv,$ll1,$ll2,$ll3,$llg,$speicheri,$speichere,$verbraucher1,$verbrauchere1
        $verbraucher2,
        $verbrauchere2,$verbraucher3,$ll4,$ll5,$ll6,$ll7,$ll8,$speichersoc,$soc,$soc1,$temp1,$temp2,$temp3,$d1,$d2,$d3,$d4,
        $d5,$d6,$d7,$d8,$d9,$d10,$temp4,$temp5,$temp6
        """
        with open('/var/www/html/openWB/web/logging/data/daily/'+file) as csv_file:
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
                            "smarthome_devices": {}
                        }
                        new_entry["cp"].update({"all": {"imported": row[7], }})
                        for i in range(1, 9):
                            new_entry_id = self.map_to_new_ids(f"cp{i}")
                            if new_entry_id is not None:
                                new_entry["cp"].update(
                                    {f"cp{new_entry_id}": {"imported": row[self.DAILY_LOG_CP_ROW_IDS[i] - 1],
                                                           "exported": 0}})
                        for i in range(1, 2):
                            new_entry_id = self.map_to_new_ids(f"ev{i}")
                            if new_entry_id is not None:
                                new_entry["ev"].update(
                                    {f"ev{new_entry_id}": {"soc": row[self.DAILY_LOG_EV_ROW_IDS[i] - 1]}})
                        new_entry["counter"].update({f"counter{self.map_to_new_ids('counter0')}": {
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
                                        "imported": row[self.DAILY_LOG_SH_TEMP_ROW_IDS[i][0] - 1],
                                        "temp0": row[self.DAILY_LOG_SH_TEMP_ROW_IDS[i][1] - 1],
                                        "temp1": row[self.DAILY_LOG_SH_TEMP_ROW_IDS[i][2] - 1],
                                        "temp2": row[self.DAILY_LOG_SH_TEMP_ROW_IDS[i][3] - 1],
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
                                        "imported": row[self.DAILY_LOG_CONSUMER_ROW_IDS[i][0] - 1],
                                        "exported": row[self.DAILY_LOG_CONSUMER_ROW_IDS[i][1] - 1]
                                    }})
                        new_entry["sh"].update({"consumer3": {"imported": row[14]}})
                    else:
                        new_entry = {}
                    yield new_entry
                except Exception:
                    pass

    MONTHLY_LOG_CP_ROW_IDS = [4, 5, 6, 12, 13, 14, 15, 16]
    MONTHLY_LOG_CONSUMER_ROW_IDS = [(8, 9), (10, 11)]

    def _monthlylog_entry_generator_func(self, file: str):
        """ Generator-Funktion, die einen Eintrag aus dem Tageslog konvertiert.
        alte Spaltenbelegung: date,$bezug,$einspeisung,$pv,$ll1,$ll2,$ll3,$llg,$verbraucher1iwh,$verbraucher1ewh,
        $verbraucher2iwh,$verbraucher2ewh,$ll4,$ll5,$ll6,$ll7,$ll8,$speicherikwh,$speicherekwh,$d1,$d2,$d3,$d4,
        $d5,$d6,$d7,$d8,$d9,$d10
        """
        with open('/var/www/html/openWB/web/logging/data/monthly/'+file) as csv_file:
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
                            "smarthome_devices": {}
                        }
                        new_entry["cp"].update({"all": {"imported": row[7], }})
                        for i in range(1, 9):
                            new_entry_id = self.map_to_new_ids(f"cp{i}")
                            if new_entry_id is not None:
                                new_entry["cp"].update(
                                    {f"cp{new_entry_id}": {"imported": row[self.MONTHLY_LOG_CP_ROW_IDS[i] - 1],
                                                           "exported": 0}})
                        new_entry["counter"].update({f"counter{self.map_to_new_ids('counter0')}": {
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
                                        "imported": row[self.MONTHLY_LOG_CONSUMER_ROW_IDS[i][0] - 1],
                                        "exported": row[self.MONTHLY_LOG_CONSUMER_ROW_IDS[i][1] - 1]
                                    }})
                    else:
                        new_entry = {}
                    yield new_entry
                except Exception:
                    pass

# convert_csv_to_json_measurement_log("monthly")
# convert_csv_to_json_measurement_log("daily")
