from decimal import Decimal
import json
import logging
import pathlib
from pathlib import Path
import re
import string
from paho.mqtt.client import Client as MqttClient, MQTTMessage
from typing import Dict, List, Tuple

from control import data
from helpermodules.broker import InternalBrokerClient
from helpermodules.pub import Pub
from helpermodules import timecheck
from control.bat import Bat
from control.chargepoint.chargepoint import Chargepoint
from control.counter import Counter
from control.ev import Ev
from control.pv import Pv
from helpermodules.utils.topic_parser import decode_payload, get_index
from modules.common.utils.component_parser import get_component_name_by_id

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
            "sh": {
                "sh1": {
                    "exported": Wh,
                    "imported": Wh,
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
            'ev': {'ev1': {}},
            'pv': {'all': {'imported': 251}, 'pv1': {'imported': 247}}},
            'sh': { 'sh1': {'exported': 123, 'imported': 123}}
        },
        "names": {
            "counter0": "Mein EVU-Zähler",
            "bat2": "Mein toller Speicher",
            ...
        }
    }

    Parameter
    ---------
    folder: str
        gibt an, ob ein Tages-oder Monats-Log-Eintrag erstellt werden soll.
    """
    if folder == "daily":
        date = timecheck.create_timestamp_time()
    else:
        date = timecheck.create_timestamp_YYYYMMDD()
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
                    {ev: {"soc": data.data.ev_data[ev].data.get.soc}})
        except Exception:
            log.exception("Fehler im Werte-Logging-Modul für EV "+str(ev))

    counter_dict = {}
    for counter in data.data.counter_data:
        try:
            if "counter" in counter:
                counter_dict.update({counter:
                                     {"imported": data.data.counter_data[counter].data.get.imported,
                                         "exported": data.data.counter_data[counter].data.get.exported}})
        except Exception:
            log.exception("Fehler im Werte-Logging-Modul für Zähler "+str(counter))

    pv_dict = {}
    if data.data.pv_all_data.data.config.configured:
        for pv in data.data.pv_data:
            try:
                pv_dict.update(
                    {pv: {"exported": data.data.pv_data[pv].data.get.exported}})
            except Exception:
                log.exception("Fehler im Werte-Logging-Modul für Wechselrichter "+str(pv))

    bat_dict = {}
    if data.data.bat_all_data.data.config.configured:
        for bat in data.data.bat_data:
            try:
                bat_dict.update({bat: {"imported": data.data.bat_data[bat].data.get.imported,
                                       "exported": data.data.bat_data[bat].data.get.exported,
                                       "soc": data.data.bat_data[bat].data.get.soc}})
            except Exception:
                log.exception("Fehler im Werte-Logging-Modul für Speicher "+str(bat))

    sh_dict, sh_names = LegacySmartHomeLogData().update()

    new_entry = {
        "timestamp": current_timestamp,
        "date": date,
        "cp": cp_dict,
        "ev": ev_dict,
        "counter": counter_dict,
        "pv": pv_dict,
        "bat": bat_dict,
        "sh": sh_dict
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
            json.dump({"entries": [], "totals": {}, "names": {}}, jsonFile)
        with open(filepath, "r") as jsonFile:
            content = json.load(jsonFile)
    entries = content["entries"]
    entries.append(new_entry)
    content["totals"] = get_totals(entries)
    content["names"] = get_names(content["totals"], sh_names)
    with open(filepath, "w") as jsonFile:
        json.dump(content, jsonFile)
    return content["totals"]


def string_to_float(value: str, default: float = 0) -> float:
    try:
        return float(value)
    except ValueError:
        return default


def string_to_int(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except ValueError:
        return default


def get_totals(entries: List, sum_up_diffs: bool = False) -> Dict:
    # beim Jahres-Log werden die Summen aus den Monatssummen berechnet, bei allen anderen aus den absoluten Zählerwerten
    totals: Dict[str, Dict] = {"cp": {}, "counter": {}, "pv": {}, "bat": {}, "sh": {}}
    prev_entry: Dict = {}
    for group in totals.keys():
        for entry in entries:
            for module in entry[group]:
                if not prev_entry or module not in totals[group]:
                    if sum_up_diffs:
                        totals[group][module] = entry[group][module]
                    else:
                        totals[group][module] = {"exported": 0} if group == "pv" else {"imported": 0, "exported": 0}
                else:
                    for key, value in entry[group][module].items():
                        if key != "soc" and "temp" not in key:
                            if value == "":
                                # Manchmal fehlen Werte im alten Log
                                value = 0
                            if sum_up_diffs:
                                value = (Decimal(str(value))
                                         + Decimal(str(totals[group][module][key])))
                            else:
                                try:
                                    prev_value = prev_entry[group][module][key]
                                # Wenn ein Modul neu hinzugefügt wurde, das es mit dieser ID schonmal gab, werden die
                                # Werte zusammen addiert.
                                except KeyError:
                                    prev_value = entry[group][module][key]
                                if prev_value == "":
                                    # Manchmal fehlen Werte im alten Log
                                    prev_value = 0
                                # avoid floating point issues with using Decimal
                                value = (Decimal(str(value))
                                         - Decimal(str(prev_value))
                                         + Decimal(str(totals[group][module][key])))
                            value = f'{value: f}'
                            # remove trailing zeros
                            totals[group][module][key] = string_to_float(
                                value) if "." in value else string_to_int(value)
            prev_entry = entry
    return totals


def get_names(totals: Dict, sh_names: Dict) -> Dict:
    names = sh_names
    for group in totals.items():
        if group[0] == "sh":
            continue
        for entry in group[1]:
            try:
                if "cp" in entry:
                    names.update({entry: data.data.cp_data[entry].data.config.name})
                elif "all" != entry:
                    id = entry.strip(string.ascii_letters)
                    names.update({entry: get_component_name_by_id(int(id))})
            except (ValueError, KeyError, AttributeError):
                names.update({entry: entry})
    return names


def get_daily_log(date: str):
    try:
        with open(str(Path(__file__).resolve().parents[2] / "data"/"daily_log"/(date+".json")), "r") as jsonFile:
            log_data = json.load(jsonFile)
            try:
                next_date = timecheck.get_relative_date_string(date, day_offset=1)
                with open(str(Path(__file__).resolve().parents[2] / "data"/"daily_log"/(next_date+".json")),
                          "r") as nextJsonFile:
                    next_log_data = json.load(nextJsonFile)
                    log_data["entries"].append(next_log_data["entries"][0])
            except FileNotFoundError:
                pass
            return log_data
    except FileNotFoundError:
        pass
    return []


def get_monthly_log(date: str):
    try:
        with open(str(Path(__file__).resolve().parents[2] / "data"/"monthly_log"/(date+".json")), "r") as jsonFile:
            log_data = json.load(jsonFile)
            try:
                next_date = timecheck.get_relative_date_string(date, month_offset=1)
                with open(str(Path(__file__).resolve().parents[2] / "data"/"monthly_log"/(next_date+".json")),
                          "r") as nextJsonFile:
                    next_log_data = json.load(nextJsonFile)
                    log_data["entries"].append(next_log_data["entries"][0])
            except FileNotFoundError:
                pass
            return log_data
    except FileNotFoundError:
        pass
    return []


def get_yearly_log(year: str):
    entries = []
    dates = []
    for month in range(1, 13):
        dates.append(f"{year}{month:02}")
    dates.append(f"{int(year)+1}01")
    for date in dates:
        try:
            with open(Path(__file__).resolve().parents[2]/"data"/"monthly_log"/f"{date}.json",
                      "r") as jsonFile:
                content = json.load(jsonFile)
                content = content["totals"]
                content.update({"date": date, "timestamp": timecheck.convert_YYYYMM_to_unix_timestamp(date)})
                entries.append(content)
        except FileNotFoundError:
            log.debug(f"Kein Log für Monat {date} gefunden.")
    return {"entries": entries, "totals": get_totals(entries, sum_up_diffs=True)}


def update_daily_yields(totals):
    """ veröffentlicht die Tageserträge für Ladepunkte, Zähler, PV und Speicher.
    """
    [update_module_yields(type, totals) for type in ("bat", "counter", "cp", "pv")]
    data.data.counter_all_data.calc_daily_yield_home_consumption()


def update_module_yields(module: str, totals: Dict) -> None:
    def update_imported_exported(daily_imported: float, daily_exported: float) -> None:
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
        module_data.data.get.daily_exported = daily_exported
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


class LegacySmartHomeLogData:
    def __init__(self) -> None:
        self.all_received_topics: Dict = {}

    def update(self) -> Tuple[Dict, Dict]:
        sh_dict: Dict = {}
        sh_names: Dict = {}
        try:
            InternalBrokerClient("smart-home-logging", self.on_connect, self.on_message).start_finite_loop()
            for topic, payload in self.all_received_topics.items():
                if re.search("openWB/LegacySmartHome/config/get/Devices/[1-9]/device_configured", topic) is not None:
                    if decode_payload(payload) == 1:
                        index = get_index(topic)
                        sh_dict.update({f"sh{index}": {}})
                        for topic, payload in self.all_received_topics.items():
                            if f"openWB/LegacySmartHome/Devices/{index}/Wh" == topic:
                                sh_dict[f"sh{index}"].update({"imported": decode_payload(payload), "exported": 0})
                            for sensor_id in range(0, 3):
                                if f"openWB/LegacySmartHome/Devices/{index}/TemperatureSensor{sensor_id}" == topic:
                                    sh_dict[f"sh{index}"].update({f"temp{sensor_id}": decode_payload(payload)})
                        for topic, payload in self.all_received_topics.items():
                            if f"openWB/LegacySmartHome/config/get/Devices/{index}/device_name" == topic:
                                sh_names.update({f"sh{index}": decode_payload(payload)})
        except Exception:
            log.exception("Fehler im Werte-Logging-Modul für SmartHome")
        finally:
            return sh_dict, sh_names

    def on_connect(self, client: MqttClient, userdata, flags: dict, rc: int):
        client.subscribe("openWB/LegacySmartHome/#", 2)

    def on_message(self, client: MqttClient, userdata, msg: MQTTMessage):
        self.all_received_topics.update({msg.topic: msg.payload})
