from enum import Enum
import json
import logging
import pathlib
from pathlib import Path
import re
import string
from paho.mqtt.client import Client as MqttClient, MQTTMessage
from typing import Dict

from control import data
from helpermodules.broker import InternalBrokerClient
from helpermodules import timecheck
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
    sh_log_data = LegacySmartHomeLogData()
    new_entry = create_entry(log_type, sh_log_data)

    # json-Objekt in Datei einfügen
    if log_type == LogType.DAILY:
        (pathlib.Path(__file__).resolve().parents[3] / "data"/"daily_log").mkdir(mode=0o755,
                                                                                 parents=True, exist_ok=True)
        filepath = str(
            Path(__file__).resolve().parents[3] / "data" / "daily_log" /
            (timecheck.create_timestamp_YYYYMMDD() + ".json"))
    else:
        (pathlib.Path(__file__).resolve().parents[3] / "data"/"monthly_log").mkdir(mode=0o755,
                                                                                   parents=True, exist_ok=True)
        filepath = str(
            Path(__file__).resolve().parents[3] / "data" / "monthly_log" /
            (timecheck.create_timestamp_YYYYMM() + ".json"))
    try:
        with open(filepath, "r") as jsonFile:
            content = json.load(jsonFile)
    except FileNotFoundError:
        with open(filepath, "w") as jsonFile:
            json.dump({"entries": [], "names": {}}, jsonFile)
        with open(filepath, "r") as jsonFile:
            content = json.load(jsonFile)
    entries = content["entries"]
    entries.append(new_entry)
    content["names"] = get_names(content["entries"][-1], sh_log_data.sh_names)
    with open(filepath, "w") as jsonFile:
        json.dump(content, jsonFile)
    return content["entries"]


def create_entry(log_type: LogType, sh_log_data: LegacySmartHomeLogData) -> Dict:
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
    for counter in data.data.counter_data:
        try:
            if "counter" in counter:
                counter_dict.update(
                    {counter: {
                        "imported": data.data.counter_data[counter].data.get.imported,
                        "exported": data.data.counter_data[counter].data.get.exported,
                        "grid": True if data.data.counter_all_data.get_evu_counter_str() == counter else False}})
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

    return {
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


def get_names(totals: Dict, sh_names: Dict) -> Dict:
    names = sh_names
    for group in totals.items():
        if group[0] not in ("bat", "counter", "cp", "pv"):
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
