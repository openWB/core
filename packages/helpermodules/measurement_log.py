

import json
import pathlib

from ..algorithm import data
from . import log
from . import pub
from . import timecheck

def save_log(folder):
    """ erstellt für jeden Tag eine Datei, die die Daten für den Langzeitgraph enthält.
    Dazu werden alle 5 Min folgende Daten als json-Liste gespeichert:
    {
        "date": str,
        "cp": {
            "cp1": {
                "counter": Zählerstand in Wh,
                }
            ... (dynamsich, je nach konfigurierter Anzahl)
            "all": {
                "counter": Zählerstand in Wh,
                }
        }
        "ev": {
            "ev1": {
                "soc": int in %
            }
            ... (dynamsich, je nach konfigurierter Anzahl)
        }
        "counter": {
            "counter0": {
                "imported": Wh,
                "exported": Wh
            }
            ... (dynamsich, je nach konfigurierter Anzahl)
        }
        "pv": {
            "all": {
                "counter": Wh
            }
            "pv0": {
                "counter": Wh
            }
            ... (dynamsich, je nach konfigurierter Anzahl)
        }
        "bat": {
            "all": {
                "imported": Wh,
                "exported": Wh,
                "soc": int in %
            }
            "bat0": {
                "imported": Wh,
                "exported": Wh,
                "soc": int in %
            }
            ... (dynamsich, je nach konfigurierter Anzahl)
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

    Parameter
    ---------
    folder: str
        gibt an, ob ein Tages-oder Monatslogeintrag erstellt werden soll.
    """
    try:
        if folder == "daily":
            date = timecheck.create_timestamp_time()
        else:
            date = timecheck.create_timestamp_YYYYMMDD()
        cp_dict = {}
        for cp in data.data.cp_data:
            try:
                if "cp" in cp:
                    cp_dict.update({cp: {"counter": data.data.cp_data[cp].data["get"]["counter"]}})
            except Exception as e:
                log.exception_logging(e)
        try:
            cp_dict.update({"all": {"counter": data.data.cp_data["all"].data["get"]["counter_all"]}})
        except Exception as e:
            log.exception_logging(e)

        ev_dict = {}
        for ev in data.data.ev_data:
            try:
                if "ev" in ev:
                    ev_dict.update({ev: {"soc": data.data.ev_data[ev].data["get"]["soc"]}})
            except Exception as e:
                log.exception_logging(e)

        counter_dict = {}
        for counter in data.data.counter_data:
            try:
                if "counter" in counter:
                    counter_dict.update({counter: {"imported": data.data.counter_data[counter].data["get"]["imported"], 
                            "exported": data.data.counter_data[counter].data["get"]["exported"]}})
            except Exception as e:
                log.exception_logging(e)

        pv_dict = {}
        for pv in data.data.pv_data:
            try:
                pv_dict.update({pv: {"imported": data.data.pv_data[pv].data["get"]["counter"]}})
            except Exception as e:
                log.exception_logging(e)

        bat_dict = {}
        for bat in data.data.bat_module_data:
            try:
                bat_dict.update({bat: {"imported": data.data.bat_module_data[bat].data["get"]["imported"],
                    "exported": data.data.bat_module_data[bat].data["get"]["exported"],
                    "soc": data.data.bat_module_data[bat].data["get"]["soc"]}})
            except Exception as e:
                log.exception_logging(e)

        new_entry = {
            "date": date,
            "cp": cp_dict,
            "ev": ev_dict,
            "counter": counter_dict,
            "pv": pv_dict,
            "bat": bat_dict
        }

        # json-Objekt in Datei einfügen
        if folder == "daily":
            pathlib.Path('./data/daily_log').mkdir(mode = 0o755, parents=True, exist_ok=True)
            filepath = "./data/daily_log/"+timecheck.create_timestamp_YYYYMMDD()+".json"
        else:
            pathlib.Path('./data/monthly_log').mkdir(mode = 0o755, parents=True, exist_ok=True)
            filepath = "./data/monthly_log/"+timecheck.create_timestamp_YYYYMM()+".json"
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

def update_daily_yields():
    """ berechnet die Tageserträge für Ladepunkte, Zähler, PV und Speicher. Dazu wird der erste Eintrag des Tageslogs (Mitternacht) vom aktuellen Zählerstand subtrahiert.
    """
    try:
        filepath = "./data/daily_log/"+timecheck.create_timestamp_YYYYMMDD()+".json"
        try:
            with open(filepath, "r") as jsonFile:
                daily_log = json.load(jsonFile)
        except FileNotFoundError:
            log.message_debug_log("error", "Fuer "+str(timecheck.create_timestamp_YYYYMMDD())+" existiert kein Tageslog.")
        # Tagesertrag Zähler
        for counter in daily_log[0]["counter"]:
            daily_yield_import = data.data.counter_data[counter].data["get"]["imported"] - daily_log[0]["counter"][counter]["imported"]
            pub.pub("openWB/set/counter/"+str(data.data.counter_data[counter].counter_num)+"/get/daily_yield_import", daily_yield_import)
            daily_yield_export = data.data.counter_data[counter].data["get"]["exported"] - daily_log[0]["counter"][counter]["exported"]
            pub.pub("openWB/set/counter/"+str(data.data.counter_data[counter].counter_num)+"/get/daily_yield_export", daily_yield_export)
        # Tagesertrag Ladepunkte
        for cp in daily_log[0]["cp"]:
            if "cp" in cp:
                daily_yield = data.data.cp_data[cp].data["get"]["counter"] - daily_log[0]["cp"][cp]["counter"]
                pub.pub("openWB/set/chargepoint/"+str(data.data.cp_data[cp].cp_num)+"/get/daily_yield", daily_yield)
            else:
                daily_yield = data.data.cp_data[cp].data["get"]["counter_all"] - daily_log[0]["cp"][cp]["counter"]
                pub.pub("openWB/set/chargepoint/get/daily_yield", daily_yield)
        # Tagesertrag PV
        for pv in daily_log[0]["pv"]:
            daily_yield = data.data.pv_data[pv].data["get"]["counter"] - daily_log[0]["pv"][pv]["imported"]
            if "pv" in pv:
                pub.pub("openWB/set/pv/"+str(data.data.pv_data[pv].pv_num)+"/get/daily_yield", daily_yield)
            else:
                pub.pub("openWB/set/pv/get/daily_yield", daily_yield)
        # Tagesertrag Speicher
        for bat in daily_log[0]["bat"]:
            daily_yield_imported = data.data.bat_module_data[bat].data["get"]["imported"] - daily_log[0]["bat"][bat]["imported"]
            if "bat" in bat:
                pub.pub("openWB/set/bat/"+str(data.data.bat_module_data[bat].bat_num)+"/get/daily_yield_import", daily_yield_imported)
            else:
                pub.pub("openWB/set/bat/get/daily_yield_import", daily_yield_imported)
            daily_yield_exported = data.data.bat_module_data[bat].data["get"]["exported"] - daily_log[0]["bat"][bat]["exported"]
            if "bat" in bat:
                pub.pub("openWB/set/bat/"+str(data.data.bat_module_data[bat].bat_num)+"/get/daily_yield_export", daily_yield_exported)
            else:
                pub.pub("openWB/set/bat/get/daily_yield_export", daily_yield_exported)
    except Exception as e:
        log.exception_logging(e)