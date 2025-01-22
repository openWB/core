from enum import Enum
import os
import json
import logging
from math import isnan
from pathlib import Path
import re
import string
from paho.mqtt.client import Client as MqttClient, MQTTMessage
from typing import Dict, Optional

from control import data
from helpermodules.broker import InternalBrokerClient
from helpermodules import timecheck
from helpermodules.utils.json_file_handler import write_and_check
from helpermodules.utils.topic_parser import decode_payload, get_index
from modules.common.utils.component_parser import get_component_name_by_id

log = logging.getLogger(__name__)

# erstellt für jeden Tag eine Datei, die die Daten für den Langzeitgraph enthält.
#     Dazu werden alle 5 Min folgende Daten als json-Liste gespeichert:
#     {"entries": [
#         {
#             "timestamp": int,
#             "date": str,
#             "cp": {
#                 "cp1": {
#                     "imported": Zählerstand in Wh,
#                     "exported": Zählerstand in Wh
#                     }
#                 ... (dynamisch, je nach konfigurierter Anzahl)
#                 "all": {
#                     "imported": Zählerstand in Wh,
#                     "exported": Zählerstand in Wh
#                     }
#             }
#             "ev": {
#                 "ev1": {
#                     "soc": int in %
#                 }
#                 ... (dynamisch, je nach konfigurierter Anzahl)
#             }
#             "counter": {
#                 "counter0": {
#                     "grid": bool,
#                     "imported": Wh,
#                     "exported": Wh
#                 }
#                 ... (dynamisch, je nach konfigurierter Anzahl)
#             }
#             "pv": {
#                 "all": {
#                     "exported": Wh
#                 }
#                 "pv0": {
#                     "exported": Wh
#                 }
#                 ... (dynamisch, je nach konfigurierter Anzahl)
#             }
#             "bat": {
#                 "all": {
#                     "imported": Wh,
#                     "exported": Wh,
#                     "soc": int in %
#                 }
#                 "bat0": {
#                     "imported": Wh,
#                     "exported": Wh,
#                     "soc": int in %
#                 }
#                 ... (dynamisch, je nach konfigurierter Anzahl)
#             }
#             "sh": {
#                 "sh1": {
#                     "exported": Wh,
#                     "imported": Wh,
#                     wenn konfiguriert:
#                     "temp1": int in °C,
#                     "temp2": int in °C,
#                     "temp3": int in °C
#                 },
#                 ... (dynamisch, je nach Anzahl konfigurierter Geräte)
#             },
#             "hc": {"all": {"imported": Wh # Hausverbrauch}}
#         }],
#      "names": "names": {"sh1": "", "cp1": "", "counter2": "", "pv3": ""}
#      }


class LogType(Enum):
    DAILY = "daily"
    MONTHLY = "monthly"


class LegacySmartHomeLogData:
    def __init__(self) -> None:
        self.all_received_topics: Dict = {}
        self.sh_dict: Dict = {}
        self.sh_names: Dict = {}
        try:
            InternalBrokerClient("smart-home-logging", self.on_connect, self.on_message).start_finite_loop()
            for topic, payload in self.all_received_topics.items():
                if re.search("openWB/LegacySmartHome/config/get/Devices/[1-9]/device_configured", topic) is not None:
                    if decode_payload(payload) == 1:
                        index = get_index(topic)
                        self.sh_dict.update({f"sh{index}": {}})
                        for topic, payload in self.all_received_topics.items():
                            if f"openWB/LegacySmartHome/Devices/{index}/Wh" == topic:
                                self.sh_dict[f"sh{index}"].update({"imported": decode_payload(payload), "exported": 0})
                            for sensor_id in range(0, 3):
                                if f"openWB/LegacySmartHome/Devices/{index}/TemperatureSensor{sensor_id}" == topic:
                                    self.sh_dict[f"sh{index}"].update({f"temp{sensor_id}": decode_payload(payload)})
                        for topic, payload in self.all_received_topics.items():
                            if f"openWB/LegacySmartHome/config/get/Devices/{index}/device_name" == topic:
                                self.sh_names.update({f"sh{index}": decode_payload(payload)})
        except Exception:
            log.exception("Fehler im Werte-Logging-Modul für SmartHome")

    def on_connect(self, client: MqttClient, userdata, flags: dict, rc: int):
        client.subscribe("openWB/LegacySmartHome/#", 2)

    def on_message(self, client: MqttClient, userdata, msg: MQTTMessage):
        self.all_received_topics.update({msg.topic: msg.payload})


def save_log(log_type: LogType):
    """ Parameter
    ---------
    folder: str
        gibt an, ob ein Tages-oder Monats-Log-Eintrag erstellt werden soll.
    """
    try:
        parent_file = Path(__file__).resolve().parents[3] / "data" / \
            ("daily_log" if log_type == LogType.DAILY else "monthly_log")
        parent_file.mkdir(mode=0o755, parents=True, exist_ok=True)
        if log_type == LogType.DAILY:
            file_name = timecheck.create_timestamp_YYYYMMDD()
        else:
            file_name = timecheck.create_timestamp_YYYYMM()
        filepath = str(parent_file / f"{file_name}.json")

        try:
            with open(filepath, "r") as jsonFile:
                content = json.load(jsonFile)
        except FileNotFoundError:
            content = {"entries": [], "names": {}}
        except json.JSONDecodeError:
            new_filepath = str(parent_file / f"{file_name}_invalid.json")
            os.rename(filepath, new_filepath)
            content = {"entries": [], "names": {}}

        previous_entry = get_previous_entry(parent_file, content)

        sh_log_data = LegacySmartHomeLogData()
        new_entry = create_entry(log_type, sh_log_data, previous_entry)

        # json-Objekt in Datei einfügen

        entries = content["entries"]
        entries.append(new_entry)
        content["names"] = get_names(content["entries"][-1], sh_log_data.sh_names)
        write_and_check(filepath, content)
        return content["entries"]
    except Exception:
        log.exception("Fehler beim Speichern des Log-Eintrags")
        return None


def get_previous_entry(parent_file: Path, content: Dict) -> Optional[Dict]:
    try:
        previous_entry = content["entries"][-1]
    except IndexError:
        # get all files in Folder
        path_list = parent_file.glob('*.json')
        # sort path list by name
        path_list = sorted(path_list, key=lambda x: x.name)
        try:
            with open(path_list[-2], "r") as jsonFile:
                content = json.load(jsonFile)
            previous_entry = content["entries"][-1]
        except (IndexError, FileNotFoundError, json.decoder.JSONDecodeError):
            previous_entry = None
    return previous_entry


def create_entry(log_type: LogType, sh_log_data: LegacySmartHomeLogData, previous_entry: Optional[Dict]) -> Dict:
    if log_type == LogType.DAILY:
        date = timecheck.create_timestamp_HH_MM()
    else:
        date = timecheck.create_timestamp_YYYYMMDD()
    current_timestamp = int(timecheck.create_timestamp())
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
    for counter in data.data.counter_data.values():
        try:
            home_consumption_source_id = data.data.counter_all_data.data.config.home_consumption_source_id
            if (home_consumption_source_id is None or counter.num != home_consumption_source_id):
                counter_dict.update(
                    {f"counter{counter.num}": {
                        "imported": counter.data.get.imported,
                        "exported": counter.data.get.exported,
                        "grid": True if data.data.counter_all_data.get_id_evu_counter() == counter.num else False}})
        except Exception:
            log.exception("Fehler im Werte-Logging-Modul für Zähler "+str(counter))

    pv_dict = {"all": {"exported": data.data.pv_all_data.data.get.exported}}
    if data.data.pv_all_data.data.config.configured:
        for pv in data.data.pv_data:
            try:
                pv_dict.update(
                    {pv: {"exported": data.data.pv_data[pv].data.get.exported}})
            except Exception:
                log.exception("Fehler im Werte-Logging-Modul für Wechselrichter "+str(pv))

    bat_dict = {"all": {"imported": data.data.bat_all_data.data.get.imported,
                        "exported": data.data.bat_all_data.data.get.exported,
                        "soc": data.data.bat_all_data.data.get.soc}}
    if data.data.bat_all_data.data.config.configured:
        for bat in data.data.bat_data:
            try:
                bat_dict.update({bat: {"imported": data.data.bat_data[bat].data.get.imported,
                                       "exported": data.data.bat_data[bat].data.get.exported,
                                       "soc": data.data.bat_data[bat].data.get.soc}})
            except Exception:
                log.exception("Fehler im Werte-Logging-Modul für Speicher "+str(bat))

    hc_dict = {"all": {"imported": data.data.counter_all_data.data.set.imported_home_consumption}}
    new_entry = {
        "timestamp": current_timestamp,
        "date": date,
        "cp": cp_dict,
        "ev": ev_dict,
        "counter": counter_dict,
        "pv": pv_dict,
        "bat": bat_dict,
        "sh": sh_log_data.sh_dict,
        "hc": hc_dict
    }

    return fix_values(new_entry, previous_entry)


def fix_values(new_entry: Dict, previous_entry: Optional[Dict]) -> Dict:
    def find_and_fix_value(value_name):
        if value.get(value_name) is not None:
            if value[value_name] == 0:
                try:
                    if (previous_entry[group][component][value_name] is not None and
                            isnan(previous_entry[group][component][value_name]) is False):
                        value[value_name] = previous_entry[group][component][value_name]
                except KeyError:
                    log.exception("Es konnte kein vorheriger Wert gefunden werden.")
    if previous_entry is not None:
        for group, value in new_entry.items():
            if group not in ("bat", "counter", "cp", "pv", "hc"):
                continue
            for component, value in value.items():
                find_and_fix_value("exported")
                find_and_fix_value("imported")
    else:
        log.warning("Keine vorherigen Werte vorhanden, um aktuelle Werte auf Plausibilität zu prüfen.")
    return new_entry


def get_names(elements: Dict, sh_names: Dict, valid_names: Optional[Dict] = None) -> Dict:
    """ Ermittelt die Namen der Komponenten, Fahrzeuge, Ladepunkte und SmartHome-Geräte, welche
    in elements vorhanden sind und gibt diese als Dictionary zurück.
    Parameter
    ---------
    elements: dict
        Dictionary, das die Messwerte enthält.
    sh_names: dict
        Dictionary, das die Namen der SmartHome-Geräte enthält.
    valid_names: dict
        Dictionary mit allen gültigen Namen, die in der Konfiguration hinterlegt sind.
        Ist None, wenn die Namen aus data ermittelt werden sollen.
    """
    names = sh_names
    for group in elements.items():
        if group[0] not in ("bat", "counter", "cp", "pv", "ev", "sh"):
            continue
        for entry in group[1]:
            # valid_names wird aus update_config übergeben, da dort noch kein Zugriff auf data möglich ist
            if valid_names is not None:
                if "all" != entry:
                    if entry in valid_names and (entry not in names or names[entry] == entry):
                        names.update({entry: valid_names[entry]})
                    else:
                        names.update({entry: entry})
            else:
                if group[0] == "sh":
                    continue
                try:
                    if "ev" in entry:
                        names.update({entry: data.data.ev_data[entry].data.name})
                    elif "cp" in entry:
                        names.update({entry: data.data.cp_data[entry].data.config.name})
                    elif "all" != entry:
                        id = entry.strip(string.ascii_letters)
                        names.update({entry: get_component_name_by_id(int(id))})
                except (ValueError, KeyError, AttributeError):
                    names.update({entry: entry})
    return names
