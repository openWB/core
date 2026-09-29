
import logging
from math import isnan
import re

from paho.mqtt.client import Client as MqttClient, MQTTMessage
from typing import Dict, Optional, Union

from control import data
from helpermodules.broker import BrokerClient
from helpermodules import timecheck
from helpermodules.utils.topic_parser import decode_payload, get_index
log = logging.getLogger(__name__)


class LegacySmartHomeLogData:
    def __init__(self) -> None:
        self.all_received_topics: Dict = {}
        self.sh_dict: Dict = {}
        self.sh_names: Dict = {}
        try:
            BrokerClient("smart-home-logging", self.on_connect, self.on_message).start_finite_loop()
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


def create_entry(sh_log_data: LegacySmartHomeLogData, previous_entry: Optional[Dict]) -> Dict:
    date = timecheck.create_timestamp_HH_MM()
    current_timestamp = int(timecheck.create_timestamp())

    try:
        prices = data.data.general_data.data.prices
        try:
            grid_price = data.data.optional_data.ep_get_current_price()
            fault_state = max(data.data.optional_data.data.electricity_pricing.flexible_tariff.get.fault_state,
                              data.data.optional_data.data.electricity_pricing.grid_fee.get.fault_state)
        except Exception:
            grid_price = prices.grid
            fault_state = 0
        prices_dict = {"grid": grid_price,
                       "pv": prices.pv,
                       "bat": prices.bat,
                       "cp": prices.cp,
                       "fault_state": fault_state}
    except Exception:
        log.exception("Fehler im Werte-Logging-Modul für Preise")
        prices_dict = {"fault_state": 0}

    try:
        cp_dict = {"all": {"imported": data.data.cp_all_data.data.get.imported,
                           "exported": data.data.cp_all_data.data.get.exported,
                           "fault_state": data.data.cp_all_data.data.get.fault_state}}
    except Exception:
        log.exception("Fehler im Werte-Logging-Modul")
        cp_dict = {}
    for cp in data.data.cp_data:
        try:
            if "cp" in cp:
                cp_dict.update({cp: {"imported": data.data.cp_data[cp].data.get.imported,
                                     "exported": data.data.cp_data[cp].data.get.exported,
                                     "fault_state": data.data.cp_data[cp].data.get.fault_state}})
        except Exception:
            log.exception("Fehler im Werte-Logging-Modul für Ladepunkt "+str(cp))

    ev_dict = {}
    for ev in data.data.ev_data:
        try:
            if "ev" in ev:
                ev_dict.update(
                    {ev: {"soc": data.data.ev_data[ev].data.get.soc,
                          "fault_state": data.data.ev_data[ev].data.get.fault_state}})
        except Exception:
            log.exception("Fehler im Werte-Logging-Modul für EV "+str(ev))

    counter_dict = {}
    counter_all_data = data.data.counter_all_data
    # Zählt alle effektiven Hausverbrauchs-Zähler, auch bei Auto-Vererbung über den Parent.
    is_home_consumption_by_counter = {}
    for current_counter in data.data.counter_data.values():
        try:
            is_home_consumption_by_counter[current_counter.num] = counter_all_data.is_home_consumption_counter(
                current_counter.num)
        except Exception:
            log.exception("Fehler beim Ermitteln der Hausverbrauchszähler.")
            is_home_consumption_by_counter[current_counter.num] = False

    home_consumption_counter_count = sum(1 for is_hc in is_home_consumption_by_counter.values() if is_hc)

    for counter in data.data.counter_data.values():
        try:
            # Der EVU-Zähler muss immer geloggt werden, unabhängig von Hausverbrauchs- oder
            # extra_meter-Zuordnung - sonst findet process_log.get_grid_counter() keinen Netzzähler mehr.
            is_grid_counter = counter_all_data.get_id_evu_counter() == counter.num
            is_home_consumption_counter = is_home_consumption_by_counter.get(counter.num, False)
            if not is_grid_counter and is_home_consumption_counter and home_consumption_counter_count == 1:
                continue
            skip_counter = False
            if not is_grid_counter:
                for consumer in data.data.consumer_data:
                    if counter.num == data.data.consumer_data[consumer].data.extra_meter:
                        skip_counter = True
                        break
            if skip_counter is False:
                counter_dict.update(
                    {f"counter{counter.num}": {
                        "imported": counter.data.get.imported,
                        "exported": counter.data.get.exported,
                        "grid": is_grid_counter,
                        "fault_state": counter.data.get.fault_state}})
        except Exception:
            log.exception("Fehler im Werte-Logging-Modul für Zähler "+str(counter))

    try:
        pv_dict = {"all": {"exported": data.data.pv_all_data.data.get.exported,
                           "fault_state": data.data.pv_all_data.data.get.fault_state}}
    except Exception:
        log.exception("Fehler im Werte-Logging-Modul für PV-Daten")
        pv_dict = {}
    if data.data.pv_all_data.data.config.configured:
        for pv in data.data.pv_data:
            try:
                pv_dict.update(
                    {pv: {"exported": data.data.pv_data[pv].data.get.exported,
                          "fault_state": data.data.pv_data[pv].data.get.fault_state}})
            except Exception:
                log.exception("Fehler im Werte-Logging-Modul für Wechselrichter "+str(pv))

    try:
        bat_dict = {"all": {"imported": data.data.bat_all_data.data.get.imported,
                            "exported": data.data.bat_all_data.data.get.exported,
                            "soc": data.data.bat_all_data.data.get.soc,
                            "fault_state": data.data.bat_all_data.data.get.fault_state}}
    except Exception:
        log.exception("Fehler im Werte-Logging-Modul für Batteriespeicher-Daten")
        bat_dict = {}
    if data.data.bat_all_data.data.config.configured:
        for bat in data.data.bat_data:
            try:
                bat_dict.update({bat: {"imported": data.data.bat_data[bat].data.get.imported,
                                       "exported": data.data.bat_data[bat].data.get.exported,
                                       "soc": data.data.bat_data[bat].data.get.soc,
                                       "fault_state": data.data.bat_data[bat].data.get.fault_state}})
            except Exception:
                log.exception("Fehler im Werte-Logging-Modul für Speicher "+str(bat))

    try:
        consumer_dict: Dict[str, Dict[str, Union[float, int]]] = {"all": {
            "imported": data.data.consumer_all_data.data.get.imported,
            "exported": data.data.consumer_all_data.data.get.exported,
            "fault_state": data.data.consumer_all_data.data.get.fault_state}}
    except Exception:
        log.exception("Fehler im Werte-Logging-Modul für Verbraucher-Daten")
        consumer_dict = {}
    for consumer in data.data.consumer_data:
        try:
            consumer_dict.update({consumer: {"imported": data.data.consumer_data[consumer].data.get.imported,
                                             "exported": data.data.consumer_data[consumer].data.get.exported,
                                             "fault_state": data.data.consumer_data[consumer].data.get.fault_state}})
        except Exception:
            log.exception("Fehler im Werte-Logging-Modul für Verbraucher "+str(consumer))

    try:
        hc_dict = {"all": {
            "imported": data.data.counter_all_data.data.set.imported_home_consumption,
            "fault_state": 2 if data.data.counter_all_data.data.set.invalid_home_consumption >= 3 else 0}}
    except Exception:
        log.exception("Fehler im Werte-Logging-Modul für Hausverbrauch")
        hc_dict = {}
    new_entry = {
        "timestamp": current_timestamp,
        "date": date,
        "prices": prices_dict,
        "cp": cp_dict,
        "ev": ev_dict,
        "counter": counter_dict,
        "pv": pv_dict,
        "bat": bat_dict,
        "consumer": consumer_dict,
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
