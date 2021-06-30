

import json
import pathlib

import data
import log
import timecheck

def save_daily_log():
    """ erstellt für jeden Tag eine Datei, die die Daten für den Langzeitgraph enthält.
    Dazu werden alle 5 Min folgende Daten als json-Liste gespeichert:
    {
        "date": str,
        "cp": {
            "cp1": {
                "counter": Zählerstand in Wh,
                }
            ... (dynamsich, je nach Anzahl konfigurierter Ladepunkte)
        }
        "ev": {
            "ev1": {
                "soc": int in %
            }
            ... (dynamsich, je nach Anzahl konfigurierter Ladepunkte)
        }
        "counter0": {
            "imported": Wh,
            "exported": Wh
        }
        "pv_all": Wh
        "bat_all": {
            "imported": Wh,
            "exported": Wh,
            "soc": int in %
        }
        "smarthome_devices": {
            "device1": {
                "counter": Wh,
                wenn konfiguriert:
                "temp1": int in °C,
                "temp2": int in °C,
                "temp3": int in °C
            },
            ... (dynamsich, je nach Anzahl konfigurierter Geräte)
        }
    }
    """
    try:
        cp_dict = {}
        for cp in data.data.cp_data:
            try:
                if "cp" in cp:
                    cp_dict.update({cp: {"counter": data.data.cp_data[cp].data["get"]["counter"]}})
            except Exception as e:
                log.exception_logging(e)

        ev_dict = {}
        for ev in data.data.ev_data:
            try:
                if "ev" in ev:
                    ev_dict.update({ev: {"soc": data.data.ev_data[ev].data["get"]["soc"]}})
            except Exception as e:
                log.exception_logging(e)

        new_entry = {
            "date": timecheck.create_timestamp_time(),
            "cp": cp_dict,
            "ev": ev_dict,
            "counter0": {
                "imported": data.data.counter_data["counter0"].data["get"]["imported"],
                "exported": data.data.counter_data["counter0"].data["get"]["exported"]
            },
            "pv_all": data.data.pv_data["all"].data["get"]["counter"],
            "bat_all": {
                "imported": data.data.bat_module_data["all"].data["get"]["imported"],
                "exported": data.data.bat_module_data["all"].data["get"]["exported"],
                "soc": data.data.bat_module_data["all"].data["get"]["soc"]
            }
        }

        # json-Objekt in Datei einfügen
        pathlib.Path('./data/daily_log').mkdir(mode = 0o755, parents=True, exist_ok=True)
        filepath = "./data/daily_log/"+timecheck.create_timestamp_YYYYMMDD()+".json"
        try:
            with open(filepath, "r") as jsonFile:
                content = json.load(jsonFile)
        except FileNotFoundError:
            with open(filepath, "w") as jsonFile:
                json.dump([], jsonFile)
            with open(filepath, "r") as jsonFile:
                content = json.load(jsonFile)
        content.append(new_entry)
        with open(filepath, "w") as jsonFile:
            json.dump(content, jsonFile)
    except Exception as e:
        log.exception_logging(e)
