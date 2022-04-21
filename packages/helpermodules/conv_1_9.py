""" Konvertierungsmodul von 1.9x nach 2.x
Konvertiert die Lade- und Tageslog-Dateien von csv nach json.
Falls nötig, ohne Abhängigkeit zur sonstigen 2.x-Implementierung.
"""

import csv
import datetime
import json
import math
import os
import pathlib

try:
    from . import data
except Exception:
    pass


class StreamArray(list):
    """
    Converts a generator into a list object that can be json serialisable
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


def conv_1_9_datetimes(datetime_str):
    """ knovertiert Datum-Uhrzeit aus 1.9x in das Format in 2.x

    Parameter
    ---------
    datetime_str: str
        Datum-Uhrzeit aus 1.9x im Format %d.%m.%y-%H:%M 05.03.21-11:16
    Return
    ------
    str
        Datum-Uhrzeit in 2.x im Format %m/%d/%Y, %H:%M 08/04/2021, 15:50
    """
    str_date = datetime.datetime.strptime(datetime_str, '%d.%m.%y-%H:%M')
    return datetime.datetime.strftime(str_date, "%m/%d/%Y, %H:%M")


def truncate(number, decimals=0):
    """
    Returns a value truncated to a specific number of decimal places.
    """
    try:
        if not isinstance(decimals, int):
            raise TypeError("decimal places must be an integer.")
        elif decimals < 0:
            raise ValueError("decimal places has to be 0 or more.")
        elif decimals == 0:
            return math.trunc(number)

        factor = 10.0 ** decimals
        return math.trunc(number * factor) / factor
    except Exception:
        pass


def convert_csv_to_json_chargelog():
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
                generator_handle = _chargelogfile_entry_generator_func(file)
                stream_array = StreamArray(generator_handle)
                for entry in json.JSONEncoder().iterencode(stream_array):
                    f.write(entry)
        except Exception:
            pass


def _chargelogfile_entry_generator_func(file):
    """ Generator-Funktion, die einen Eintrag aus dem Ladelog konvertiert.

    Parameter:
    file: csv-Datei
        csv-Datei, deren Einträge konvertiert werden sollen.
    """
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
                        costs = data.data.general_data["general"].data["price_kwh"] * row[3]
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
                            "charged_since_mode_switch": 0,
                            "imported_since_plugged": float(row[3]),
                            "power": float(row[4]),
                            "costs": truncate(costs, 2)
                        }
                    }
                else:
                    new_entry = {}
                yield new_entry

            except Exception:
                pass


def convert_csv_to_json_measurement_log(folder):
    """ konvertiert die alten Tages- und Monatslog-Dateien in das neue Format für 2.x.

    Parameter
    ---------
    folder: str
        Ordner, der konvertiert werden soll.
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
                    generator_handle = _dailylog_entry_generator_func(file)
                else:
                    generator_handle = _monthlylog_entry_generator_func(file)
                stream_array = StreamArray(generator_handle)
                for entry in json.JSONEncoder().iterencode(stream_array):
                    f.write(entry)
        except Exception:
            pass


def _dailylog_entry_generator_func(file):
    """ Generator-Funktion, die einen Eintrag aus dem Tageslog konvertiert.
    alte Spaltenbelegung:
    date, $bezug,$einspeisung,$pv,$ll1,$ll2,$ll3,$llg,$speicheri,$speichere,$verbraucher1,$verbrauchere1,$verbraucher2,
    $verbrauchere2,$verbraucher3,$ll4,$ll5,$ll6,$ll7,$ll8,$speichersoc,$soc,$soc1,$temp1,$temp2,$temp3,$d1,$d2,$d3,$d4,
    $d5,$d6,$d7,$d8,$d9,$d10,$temp4,$temp5,$temp6

    Parameter
    ---------
    file: csv-Datei
        csv-Datei, deren Einträge konvertiert werden sollen.
    """
    with open('/var/www/html/openWB/web/logging/data/daily/'+file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            try:
                if len(row) != 0:
                    new_entry = {
                        "date": row[0][:2]+":"+row[0][-2:],
                        "cp": {
                            "all": {
                                "counter": row[7]
                            },
                            "cp1": {
                                "counter": row[4],
                            },
                            "cp2": {
                                "counter": row[5],
                            },
                            "cp3": {
                                "counter": row[6],
                            },
                            "cp4": {
                                "counter": row[15],
                            },
                            "cp5": {
                                "counter": row[16],
                            },
                            "cp6": {
                                "counter": row[17],
                            },
                            "cp7": {
                                "counter": row[18],
                            },
                            "cp8": {
                                "counter": row[19],
                            }
                        },
                        "ev": {
                            "ev1": {
                                "soc": row[21]
                            },
                            "ev2": {
                                "soc": row[22]
                            }
                        },
                        "counter": {
                            "counter0": {
                                "imported": row[1],
                                "exported": row[2]
                            }
                        },
                        "pv": {
                            "all": {
                                "counter": row[3]
                            }
                        },
                        "bat": {
                            "all": {
                                "imported": row[8],
                                "exported": row[9],
                                "soc": row[20]
                            }
                        },
                        "smarthome_devices": {
                            "device1": {
                                "counter": row[26],
                                "temp1": row[23],
                                "temp2": row[24],
                                "temp3": row[25]
                            },
                            "device2": {
                                "counter": row[27],
                                "temp1": row[36],
                                "temp2": row[37],
                                "temp3": row[38]
                            },
                            "device3": {
                                "counter": row[28]
                            },
                            "device4": {
                                "counter": row[29]
                            },
                            "device5": {
                                "counter": row[30]
                            },
                            "device6": {
                                "counter": row[31]
                            },
                            "device7": {
                                "counter": row[32]
                            },
                            "device8": {
                                "counter": row[33]
                            },
                            "device9": {
                                "counter": row[34]
                            },
                            "device10": {
                                "counter": row[35]
                            },
                            "consumer1": {
                                "imported": row[10],
                                "exported": row[11]
                            },
                            "consumer2": {
                                "imported": row[12],
                                "exported": row[13]
                            },
                            "consumer3": {
                                "imported": row[14]
                            }
                        }
                    }
                else:
                    new_entry = {}
                yield new_entry
            except Exception:
                pass


def _monthlylog_entry_generator_func(file):
    """ Generator-Funktion, die einen Eintrag aus dem Tageslog konvertiert.
    alte Spaltenbelegung: date,$bezug,$einspeisung,$pv,$ll1,$ll2,$ll3,$llg,$verbraucher1iwh,$verbraucher1ewh,
    $verbraucher2iwh,$verbraucher2ewh,$ll4,$ll5,$ll6,$ll7,$ll8,$speicherikwh,$speicherekwh,$d1,$d2,$d3,$d4,
    $d5,$d6,$d7,$d8,$d9,$d10

    Parameter
    ---------
    file: csv-Datei
        csv-Datei, deren Einträge konvertiert werden sollen.
    """
    with open('/var/www/html/openWB/web/logging/data/monthly/'+file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            try:
                if len(row) != 0:
                    new_entry = {
                        "date": row[0],
                        "cp": {
                            "all": {
                                "counter": row[7]
                            },
                            "cp1": {
                                "counter": row[4],
                            },
                            "cp2": {
                                "counter": row[5],
                            },
                            "cp3": {
                                "counter": row[6],
                            },
                            "cp4": {
                                "counter": row[12],
                            },
                            "cp5": {
                                "counter": row[13],
                            },
                            "cp6": {
                                "counter": row[14],
                            },
                            "cp7": {
                                "counter": row[15],
                            },
                            "cp8": {
                                "counter": row[16],
                            }
                        },
                        "counter": {
                            "counter0": {
                                "imported": row[1],
                                "exported": row[2]
                            }
                        },
                        "pv": {
                            "all": {
                                "counter": row[3]
                            }
                        },
                        "bat": {
                            "all": {
                                "imported": row[17],
                                "exported": row[18]
                            }
                        },
                        "smarthome_devices": {
                            "device1": {
                                "counter": row[19]
                            },
                            "device2": {
                                "counter": row[20]
                            },
                            "device3": {
                                "counter": row[21]
                            },
                            "device4": {
                                "counter": row[22]
                            },
                            "device5": {
                                "counter": row[23]
                            },
                            "device6": {
                                "counter": row[24]
                            },
                            "device7": {
                                "counter": row[25]
                            },
                            "device8": {
                                "counter": row[26]
                            },
                            "device9": {
                                "counter": row[27]
                            },
                            "device10": {
                                "counter": row[28]
                            },
                            "consumer1": {
                                "imported": row[8],
                                "exported": row[9]
                            },
                            "consumer2": {
                                "imported": row[10],
                                "exported": row[11]
                            }
                        }
                    }
                else:
                    new_entry = {}
                yield new_entry
            except Exception:
                pass

# convert_csv_to_json_measurement_log("monthly")
# convert_csv_to_json_measurement_log("daily")
