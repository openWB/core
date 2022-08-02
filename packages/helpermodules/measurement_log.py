

from decimal import Decimal
import json
import logging
import pathlib
from pathlib import Path
from typing import Dict, List

from control import data
from helpermodules.pub import Pub
from helpermodules import timecheck
from control.bat import Bat
from control.chargepoint import Chargepoint
from control.counter import Counter
from control.ev import Ev
from control.pv import Pv

log = logging.getLogger(__name__)


def measurement_log_daily():
    try:
        totals = save_log("daily")
        update_daily_yields(totals)
    except Exception:
        log.exception("Fehler im Werte-Logging-Modul")


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
                    "exported": Wh
                }
                "pv0": {
                    "exported": Wh
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
        gibt an, ob ein Tages-oder Monats-Eintrag im Protokoll erstellt werden soll.
    """
    if folder == "daily":
        date = timecheck.create_timestamp(timecheck.TimestampFormat.time)
    else:
        date = timecheck.create_timestamp(timecheck.TimestampFormat.year_month_day)
    current_timestamp = timecheck.create_timestamp_unix()
    cp_dict = {}
    for cp in data.data.cp_data:
        try:
            if "cp" in cp:
                cp_dict.update({cp: {"imported": data.data.cp_data[cp].data.get.imported,
                                     "exported": data.data.cp_data[cp].data.get.exported}})
        except Exception:
            log.exception("Fehler im Werte-Logging-Modul für Ladepunkt "+str(cp))
    try:
        cp_dict.update(
            {"all": {"imported": data.data.cp_all_data.data.get.imported,
                     "exported": data.data.cp_all_data.data.get.exported}})
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
                    {pv: {"exported": data.data.pv_data[pv].data["get"]["exported"]}})
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
            (timecheck.create_timestamp(timecheck.TimestampFormat.year_month_day) + ".json"))
    else:
        (pathlib.Path(__file__).resolve().parents[2] / "data"/"monthly_log").mkdir(mode=0o755,
                                                                                   parents=True, exist_ok=True)
        filepath = str(
            Path(__file__).resolve().parents[2] / "data" / "monthly_log" /
            (timecheck.create_timestamp(timecheck.TimestampFormat.year_month) + ".json"))
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
    return content["totals"]


def get_totals(entries: List) -> Dict:
    totals = {"cp": {}, "counter": {}, "pv": {}, "bat": {}}
    prev_entry = {}
    for group in totals.keys():
        for entry in entries:
            for module in entry[group]:
                if not prev_entry or module not in totals[group]:
                    totals[group][module] = {"exported": 0} if group == "pv" else {"imported": 0, "exported": 0}
                else:
                    for key, value in entry[group][module].items():
                        if key != "soc":
                            try:
                                prev_value = prev_entry[group][module][key]
                            # Wenn ein Modul neu hinzugefügt wurde, das es mit dieser ID bereits gab, werden die Werte
                            # zusammen addiert.
                            except KeyError:
                                prev_value = entry[group][module][key]
                            # avoid floating point issues with using Decimal
                            value = (Decimal(str(value))
                                     - Decimal(str(prev_value))
                                     + Decimal(str(totals[group][module][key])))
                            value = f'{value: f}'
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


def update_daily_yields(totals):
    """ publisht die Tageserträge für Ladepunkte, Zähler, PV und Speicher.
    """
    [update_module_yields(type, totals) for type in ("bat", "counter", "cp", "pv")]
    data.data.counter_data["all"].calc_daily_yield_home_consumption()


def update_module_yields(module: str, totals: Dict) -> None:
    def update_imported_exported(daily_imported: float, daily_exported: float) -> None:
        if isinstance(module_data.data, Dict):
            module_data.data["get"].update({"daily_imported": daily_imported, "daily_exported": daily_exported})
        else:
            module_data.data.get.daily_imported = daily_imported
            module_data.data.get.daily_exported = daily_exported
        if module == "cp":
            topic = "chargepoint"
        else:
            topic = module
        if isinstance(module_data, (Ev, Chargepoint, Pv, Bat, Counter)):
            Pub().pub(f"openWB/set/{topic}/{module_data.num}/get/daily_imported", daily_imported)
            Pub().pub(f"openWB/set/{topic}/{module_data.num}/get/daily_exported", daily_exported)
        else:
            Pub().pub(f"openWB/set/{topic}/get/daily_imported", daily_imported)
            Pub().pub(f"openWB/set/{topic}/get/daily_exported", daily_exported)

    def update_exported(daily_exported: float) -> None:
        module_data.data["get"]["daily_exported"] = daily_exported
        if module in m:
            Pub().pub(f"openWB/set/pv/{module_data.num}/get/daily_exported", daily_exported)
        else:
            Pub().pub("openWB/set/pv/get/daily_exported", daily_exported)

    for m in totals[module]:
        if m in getattr(data.data, f"{module}_data"):
            module_data = getattr(data.data, f"{module}_data")[m]
            if module == "pv":
                update_exported(totals[module][m]["exported"])
            else:
                update_imported_exported(totals[module][m]["imported"], totals[module][m]["exported"])
        else:
            log.info(f"Modul {m} wurde zwischenzeitlich gelöscht und wird daher nicht mehr aufgeführt.")
        if module == "cp" and m == "all":
            module_data = data.data.cp_all_data
            update_imported_exported(totals[module][m]["imported"], totals[module][m]["exported"])
