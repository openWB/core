

from decimal import Decimal
import json
import logging
import pathlib
from pathlib import Path
from typing import Dict, List

from control import data
from helpermodules.pub import Pub
from helpermodules import timecheck

log = logging.getLogger(__name__)


def save_log(folder):
    """ erstellt für jeden Tag eine Datei, die die Daten für den Langzeitgraph enthält.
    Dazu werden alle 5 Min folgende Daten als json-Liste gespeichert:
    {"entries": [
        {
            "timestamp": int,
            "date": str,
            "cp": {
                "cp1": {
                    "imported": Zählerstand in Wh,
                    "exported": Zählerstand in Wh
                    }
                ... (dynamisch, je nach konfigurierter Anzahl)
                "all": {
                    "imported": Zählerstand in Wh,
                    "exported": Zählerstand in Wh
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
        }],
        "totals": {
            {'bat': {'all': {'exported': 0, 'imported': 175.534},
            'bat2': {'exported': 0, 'imported': 172.556}},
            'counter': {'counter0': {'exported': 1.105, 'imported': 1.1}},
            'cp': {'all': {'exported': 0, 'imported': 105},
                    'cp3': {'exported': 0, 'imported': 10},
                    'cp4': {'exported': 0, 'imported': 85},
                    'cp5': {'exported': 0, 'imported': 0},
                    'cp6': {'exported': 0, 'imported': 64}},
            'pv': {'all': {'imported': 251}, 'pv1': {'imported': 247}}}
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
                    cp_dict.update({cp: {"imported": data.data.cp_data[cp].data["get"]["imported"],
                                         "exported": data.data.cp_data[cp].data["get"]["exported"]}})
            except Exception:
                log.exception("Fehler im Werte-Logging-Modul für Ladepunkt "+str(cp))
        try:
            cp_dict.update(
                {"all": {"imported": data.data.cp_data["all"].data["get"]["imported"],
                         "exported": data.data.cp_data["all"].data["get"]["exported"]}})
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
                json.dump({"entries": [], "totals": {}}, jsonFile)
            with open(filepath, "r") as jsonFile:
                content = json.load(jsonFile)
        entries = content["entries"]
        entries.append(new_entry)
        content["totals"] = get_totals(entries)
        with open(filepath, "w") as jsonFile:
            json.dump(content, jsonFile)
    except Exception:
        log.exception("Fehler im Werte-Logging-Modul")


def get_totals(entries: List) -> Dict:
    totals = {"cp": {}, "counter": {}, "pv": {}, "bat": {}}
    prev_entry = {}
    for group in totals.keys():
        for entry in entries:
            for module in entry[group]:
                if not prev_entry or module not in totals[group]:
                    totals[group][module] = {"imported": 0} if group == "pv" else {"imported": 0, "exported": 0}
                else:
                    for key, value in entry[group][module].items():
                        if key != "soc":
                            try:
                                prev_value = prev_entry[group][module][key]
                            # Wenn ein Modul neu hinzugefügt wurde, das es mit dieser ID schonmal gab, werden die Werte
                            # zusammen addiert.
                            except KeyError:
                                prev_value = entry[group][module][key]
                            # avoid floating point issues with using Decimal
                            value = str(Decimal(str(value)) - Decimal(str(prev_value)) +
                                        Decimal(str(totals[group][module][key])))
                            # remove trailing zeros
                            totals[group][module][key] = float(value) if "." in value else int(value)
            prev_entry = entry
    return totals


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
        last_entry = daily_log["entries"][-1]
        entry0 = daily_log["entries"][0]
        # Tagesertrag Zähler
        for c in last_entry["counter"]:
            if c in data.data.counter_data:
                counter = data.data.counter_data[c]
                daily_imported = counter.data["get"]["imported"] - entry0["counter"][c]["imported"]
                daily_exported = counter.data["get"]["exported"] - entry0["counter"][c]["exported"]
                counter.data["get"].update({"daily_imported": daily_imported, "daily_exported": daily_exported})
                Pub().pub(f"openWB/set/counter/{counter.counter_num}/get/daily_imported", daily_imported)
                Pub().pub(f"openWB/set/counter/{counter.counter_num}/get/daily_exported", daily_exported)
            else:
                log.info(f"Zähler {c} wurde zwischenzeitlich gelöscht und wird daher nicht mehr aufgeführt.")
        # Tagesertrag Ladepunkte
        for chargepoint in last_entry["cp"]:
            if chargepoint in data.data.cp_data:
                cp = data.data.cp_data[chargepoint]
                daily_imported = cp.data["get"]["imported"] - entry0["cp"][chargepoint]["imported"]
                daily_exported = cp.data["get"]["exported"] - entry0["cp"][chargepoint]["exported"]
                cp.data["get"].update({"daily_exported": daily_exported, "daily_imported": daily_imported})
                if "cp" in chargepoint:
                    Pub().pub(f"openWB/set/chargepoint/{cp.cp_num}/get/daily_imported", daily_imported)
                    Pub().pub(f"openWB/set/chargepoint/{cp.cp_num}/get/daily_exported", daily_exported)
                else:
                    Pub().pub("openWB/set/chargepoint/get/daily_imported", daily_imported)
                    Pub().pub("openWB/set/chargepoint/get/daily_exported", daily_exported)
            else:
                log.info(
                    f"Ladepunkt {chargepoint} wurde zwischenzeitlich gelöscht und wird daher nicht mehr aufgeführt.")
        # Tagesertrag PV
        for pv in last_entry["pv"]:
            if pv in data.data.pv_data:
                daily_yield = data.data.pv_data[pv].data["get"]["counter"] - entry0["pv"][pv]["imported"]
                data.data.pv_data[pv].data["get"]["daily_yield"] = daily_yield
                if "pv" in pv:
                    Pub().pub(f"openWB/set/pv/{data.data.pv_data[pv].pv_num}/get/daily_yield", daily_yield)
                else:
                    Pub().pub("openWB/set/pv/get/daily_yield", daily_yield)
            else:
                log.info(f"Wechselrichter {pv} wurde zwischenzeitlich gelöscht und wird daher nicht mehr aufgeführt.")
        # Tagesertrag Speicher
        for b in last_entry["bat"]:
            if b in data.data.bat_data:
                bat = data.data.bat_data[b]
                daily_imported = bat.data["get"]["imported"] - entry0["bat"][b]["imported"]
                daily_exported = bat.data["get"]["exported"] - entry0["bat"][b]["exported"]
                bat.data["get"].update({"daily_imported": daily_imported, "daily_exported": daily_exported})
                if "bat" in b:
                    Pub().pub(f"openWB/set/bat/{bat.bat_num}/get/daily_imported", daily_imported)
                    Pub().pub(f"openWB/set/bat/{bat.bat_num}/get/daily_exported", daily_exported)
                else:
                    Pub().pub("openWB/set/bat/get/daily_imported", daily_imported)
                    Pub().pub("openWB/set/bat/get/daily_exported", daily_exported)
            else:
                log.info(f"Speicher {b} wurde zwischenzeitlich gelöscht und wird daher nicht mehr aufgeführt.")
        data.data.counter_data["all"].calc_daily_yield_home_consumption()
    except Exception:
        log.exception("Fehler im Werte-Logging-Modul")
