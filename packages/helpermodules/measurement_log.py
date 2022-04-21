

import json
import logging
import pathlib
from pathlib import Path

from control import data
from helpermodules.pub import Pub
from helpermodules import timecheck

log = logging.getLogger(__name__)


def save_log(folder):
    """ erstellt für jeden Tag eine Datei, die die Daten für den Langzeitgraph enthält.
    Dazu werden alle 5 Min folgende Daten als json-Liste gespeichert:
    {
        "timestamp": int,
        "date": str,
        "cp": {
            "cp1": {
                "imported": Zählerstand in Wh,
                }
            ... (dynamisch, je nach konfigurierter Anzahl)
            "all": {
                "imported": Zählerstand in Wh,
                }
        }
        "ev": {
            "ev1": {
                "soc": int in %
            }
            ... (dynamisch, je nach konfigurierter Anzahl)
        }
        "counter": {
            "counter0": {
                "imported": Wh,
                "exported": Wh
            }
            ... (dynamisch, je nach konfigurierter Anzahl)
        }
        "pv": {
            "all": {
                "counter": Wh
            }
            "pv0": {
                "counter": Wh
            }
            ... (dynamisch, je nach konfigurierter Anzahl)
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
            ... (dynamisch, je nach konfigurierter Anzahl)
        }
        "smarthome_devices": {
            "device1": {
                "counter": Wh,
                wenn konfiguriert:
                "temp1": int in °C,
                "temp2": int in °C,
                "temp3": int in °C
            },
            ... (dynamisch, je nach Anzahl konfigurierter Geräte)
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
        current_timestamp = timecheck.create_timestamp_unix()
        cp_dict = {}
        for cp in data.data.cp_data:
            try:
                if "cp" in cp:
                    cp_dict.update(
                        {cp: {"imported": data.data.cp_data[cp].data["get"]["imported"]}})
            except Exception:
                log.exception("Fehler im Werte-Logging-Modul für Ladepunkt "+str(cp))
        try:
            cp_dict.update(
                {"all": {"imported": data.data.cp_data["all"].data["get"]["imported"]}})
        except Exception:
            log.exception("Fehler im Werte-Logging-Modul")

        ev_dict = {}
        for ev in data.data.ev_data:
            try:
                if "ev" in ev:
                    ev_dict.update(
                        {ev: {"soc": data.data.ev_data[ev].data["get"]["soc"]}})
            except Exception:
                log.exception("Fehler im Werte-Logging-Modul für EV "+str(ev))

        counter_dict = {}
        for counter in data.data.counter_data:
            try:
                if "counter" in counter:
                    counter_dict.update({counter:
                                         {"imported": data.data.counter_data[counter].data["get"]["imported"],
                                          "exported": data.data.counter_data[counter].data["get"]["exported"]}})
            except Exception:
                log.exception("Fehler im Werte-Logging-Modul für Zähler "+str(counter))

        pv_dict = {}
        if data.data.pv_data["all"].data["config"]["configured"]:
            for pv in data.data.pv_data:
                try:
                    pv_dict.update(
                        {pv: {"imported": data.data.pv_data[pv].data["get"]["counter"]}})
                except Exception:
                    log.exception("Fehler im Werte-Logging-Modul für Wechselrichter "+str(pv))

        bat_dict = {}
        if data.data.bat_data["all"].data["config"]["configured"]:
            for bat in data.data.bat_data:
                try:
                    bat_dict.update({bat: {"imported": data.data.bat_data[bat].data["get"]["imported"],
                                           "exported": data.data.bat_data[bat].data["get"]["exported"],
                                           "soc": data.data.bat_data[bat].data["get"]["soc"]}})
                except Exception:
                    log.exception("Fehler im Werte-Logging-Modul für Speicher "+str(bat))

        new_entry = {
            "timestamp": current_timestamp,
            "date": date,
            "cp": cp_dict,
            "ev": ev_dict,
            "counter": counter_dict,
            "pv": pv_dict,
            "bat": bat_dict
        }

        # json-Objekt in Datei einfügen
        if folder == "daily":
            (pathlib.Path(__file__).resolve().parents[2] / "data"/"daily_log").mkdir(mode=0o755,
                                                                                     parents=True, exist_ok=True)
            filepath = str(
                Path(__file__).resolve().parents[2] / "data" / "daily_log" /
                (timecheck.create_timestamp_YYYYMMDD() + ".json"))
        else:
            (pathlib.Path(__file__).resolve().parents[2] / "data"/"monthly_log").mkdir(mode=0o755,
                                                                                       parents=True, exist_ok=True)
            filepath = str(
                Path(__file__).resolve().parents[2] / "data" / "monthly_log" /
                (timecheck.create_timestamp_YYYYMM() + ".json"))
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
    except Exception:
        log.exception("Fehler im Werte-Logging-Modul")


def get_daily_log(date: str):
    try:
        with open(str(Path(__file__).resolve().parents[2] / "data"/"daily_log"/(date+".json")), "r") as jsonFile:
            return json.load(jsonFile)
    except FileNotFoundError:
        pass
    return []


def get_monthly_log(date: str):
    try:
        with open(str(Path(__file__).resolve().parents[2] / "data"/"monthly_log"/(date+".json")), "r") as jsonFile:
            return json.load(jsonFile)
    except FileNotFoundError:
        pass
    return []


def update_daily_yields():
    """ berechnet die Tageserträge für Ladepunkte, Zähler, PV und Speicher. Dazu wird der erste Eintrag des Tages-Logs
    (Mitternacht) vom aktuellen Zählerstand subtrahiert.
    """
    try:
        filepath = str(
            Path(__file__).resolve().parents[2] / "data" / "daily_log" /
            (timecheck.create_timestamp_YYYYMMDD() + ".json"))
        try:
            with open(filepath, "r") as jsonFile:
                daily_log = json.load(jsonFile)
        except FileNotFoundError:
            raise FileNotFoundError(
                "Für "+str(timecheck.create_timestamp_YYYYMMDD())+" existiert kein Tageslog.")
        # Tagesertrag Zähler
        for counter in daily_log[0]["counter"]:
            if counter in data.data.counter_data:
                daily_yield_imported = data.data.counter_data[counter].data["get"]["imported"] - \
                    daily_log[0]["counter"][counter]["imported"]
                data.data.counter_data[counter].data["get"]["daily_imported"] = daily_yield_imported
                Pub().pub("openWB/set/counter/"+str(
                    data.data.counter_data[counter].counter_num)+"/get/daily_imported", daily_yield_imported)
                daily_yield_exported = data.data.counter_data[counter].data["get"]["exported"] - \
                    daily_log[0]["counter"][counter]["exported"]
                data.data.counter_data[counter].data["get"]["daily_exported"] = daily_yield_exported
                Pub().pub("openWB/set/counter/"+str(
                    data.data.counter_data[counter].counter_num)+"/get/daily_exported", daily_yield_exported)
            else:
                log.info("Zähler "+str(counter) +
                         " wurde zwischenzeitlich gelöscht und wird daher nicht mehr aufgeführt.")
        # Tagesertrag Ladepunkte
        for cp in daily_log[0]["cp"]:
            if cp in data.data.cp_data:
                daily_yield = data.data.cp_data[cp].data["get"]["imported"] - \
                    daily_log[0]["cp"][cp]["imported"]
                data.data.cp_data[cp].data["get"]["daily_yield"] = daily_yield
                if "cp" in cp:
                    Pub().pub("openWB/set/chargepoint/" +
                              str(data.data.cp_data[cp].cp_num)+"/get/daily_yield", daily_yield)
                else:
                    Pub().pub("openWB/set/chargepoint/get/daily_yield", daily_yield)
            else:
                log.info("Ladepunkt "+str(cp) +
                         " wurde zwischenzeitlich gelöscht und wird daher nicht mehr aufgeführt.")
        # Tagesertrag PV
        for pv in daily_log[0]["pv"]:
            if pv in data.data.pv_data:
                daily_yield = data.data.pv_data[pv].data["get"]["counter"] - \
                    daily_log[0]["pv"][pv]["imported"]
                data.data.pv_data[pv].data["get"]["daily_yield"] = daily_yield
                if "pv" in pv:
                    Pub().pub(
                        "openWB/set/pv/"+str(data.data.pv_data[pv].pv_num)+"/get/daily_yield", daily_yield)
                else:
                    Pub().pub("openWB/set/pv/get/daily_yield", daily_yield)
            else:
                log.info("Wechselrichter "+str(pv) +
                         " wurde zwischenzeitlich gelöscht und wird daher nicht mehr aufgeführt.")
        # Tagesertrag Speicher
        for bat in daily_log[0]["bat"]:
            if bat in data.data.bat_data:
                daily_yield_importeded = data.data.bat_data[bat].data["get"]["imported"] - \
                    daily_log[0]["bat"][bat]["imported"]
                daily_yield_exporteded = data.data.bat_data[bat].data["get"]["exported"] - \
                    daily_log[0]["bat"][bat]["exported"]
                data.data.bat_data[bat].data["get"]["daily_imported"] = daily_yield_importeded
                data.data.bat_data[bat].data["get"]["daily_exported"] = daily_yield_exporteded
                if "bat" in bat:
                    Pub().pub("openWB/set/bat/"+str(
                        data.data.bat_data[bat].bat_num)+"/get/daily_imported", daily_yield_importeded)
                    Pub().pub("openWB/set/bat/"+str(
                        data.data.bat_data[bat].bat_num)+"/get/daily_exported", daily_yield_exporteded)
                else:
                    Pub().pub("openWB/set/bat/get/daily_imported",
                              daily_yield_importeded)
                    Pub().pub("openWB/set/bat/get/daily_exported",
                              daily_yield_exporteded)
            else:
                log.info("Speicher "+str(bat) +
                         " wurde zwischenzeitlich gelöscht und wird daher nicht mehr aufgeführt.")
        data.data.counter_data["all"].calc_daily_yield_home_consumption()
    except Exception:
        log.exception("Fehler im Werte-Logging-Modul")
