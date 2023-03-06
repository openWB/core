""" Modul, um die Daten vom Broker zu erhalten.
"""
import importlib
import json
import logging
from pathlib import Path
import threading
from typing import Dict
import re
import subprocess
import paho.mqtt.client as mqtt

from control import bat_all, bat, pv_all
from control import chargepoint
from control import counter
from control import counter_all
from control import ev
from control import general
from helpermodules import graph
from helpermodules.abstract_plans import AutolockPlan
from helpermodules.broker import InternalBrokerClient
from helpermodules.messaging import MessageType, pub_system_message
from helpermodules.utils.topic_parser import decode_payload, get_index, get_second_index
from control import optional
from helpermodules.pub import Pub
from helpermodules import system
from control import pv
from dataclass_utils import dataclass_from_dict
from modules.common.simcount.simcounter_state import SimCounterState

log = logging.getLogger(__name__)
mqtt_log = logging.getLogger("mqtt")


class SubData:
    """ Klasse, die die benötigten Topics abonniert, die Instanzen erstellt, wenn z.b. ein Modul neu konfiguriert
    wird, Instanzen löscht, wenn Module gelöscht werden, und die Werte in die Attribute der Instanzen schreibt.
    """

    # Instanzen
    cp_data: Dict[str, chargepoint.Chargepoint] = {}
    cp_all_data = chargepoint.AllChargepoints()
    cp_template_data: Dict[str, chargepoint.CpTemplate] = {}
    pv_data: Dict[str, pv.Pv] = {}
    pv_all_data = pv_all.PvAll()
    ev_data: Dict[str, ev.Ev] = {}
    ev_template_data: Dict[str, ev.EvTemplate] = {}
    ev_charge_template_data: Dict[str, ev.ChargeTemplate] = {}
    counter_data: Dict[str, counter.Counter] = {}
    counter_all_data = counter_all.CounterAll()
    bat_all_data = bat_all.BatAll()
    bat_data: Dict[str, bat.Bat] = {}
    general_data = general.General()
    optional_data = optional.Optional()
    system_data = {}
    graph_data = graph.Graph()

    def __init__(self,
                 event_ev_template: threading.Event,
                 event_charge_template: threading.Event,
                 event_cp_config: threading.Event,
                 event_module_update_completed: threading.Event,
                 event_copy_data: threading.Event,
                 event_global_data_initialized: threading.Event,
                 event_command_completed: threading.Event,
                 event_subdata_initialized: threading.Event,
                 event_vehicle_update_completed: threading.Event):
        self.event_ev_template = event_ev_template
        self.event_charge_template = event_charge_template
        self.event_cp_config = event_cp_config
        self.event_module_update_completed = event_module_update_completed
        self.event_copy_data = event_copy_data
        self.event_global_data_initialized = event_global_data_initialized
        self.event_command_completed = event_command_completed
        self.event_subdata_initialized = event_subdata_initialized
        self.event_vehicle_update_completed = event_vehicle_update_completed
        self.heartbeat = False

    def sub_topics(self):
        self.internal_broker_client = InternalBrokerClient("mqttsub", self.on_connect, self.on_message)
        self.internal_broker_client.start_infinite_loop()

    def disconnect(self) -> None:
        self.internal_broker_client.disconnect()

    def on_connect(self, client: mqtt.Client, userdata, flags: dict, rc: int):
        """ subscribe topics
        """
        client.subscribe([
            ("openWB/vehicle/#", 2),
            ("openWB/chargepoint/#", 2),
            ("openWB/pv/#", 2),
            ("openWB/bat/#", 2),
            ("openWB/general/#", 2),
            ("openWB/graph/#", 2),
            ("openWB/optional/#", 2),
            ("openWB/counter/#", 2),
            ("openWB/command/command_completed", 2),
            # Nicht mit hash # abonnieren, damit nicht die Komponenten vor den Devices empfangen werden!
            ("openWB/system/+", 2),
            ("openWB/system/device/module_update_completed", 2),
            ("openWB/system/mqtt/bridge/+", 2),
            ("openWB/system/device/+/config", 2),
        ])
        Pub().pub("openWB/system/subdata_initialized", True)

    def on_message(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
        """ wait for incoming topics.
        """
        mqtt_log.debug("Topic: "+str(msg.topic) +
                       ", Payload: "+str(msg.payload.decode("utf-8")))
        self.heartbeat = True
        if "openWB/vehicle/template/charge_template/" in msg.topic:
            self.process_vehicle_charge_template_topic(
                self.ev_charge_template_data, msg)
        elif "openWB/vehicle/template/ev_template/" in msg.topic:
            self.process_vehicle_ev_template_topic(self.ev_template_data, msg)
        elif "openWB/vehicle/" in msg.topic:
            self.process_vehicle_topic(self.ev_data, msg)
        elif "openWB/chargepoint/template/" in msg.topic:
            self.process_chargepoint_template_topic(self.cp_template_data, msg)
        elif "openWB/chargepoint/" in msg.topic:
            self.process_chargepoint_topic(self.cp_data, msg)
        elif "openWB/pv/" in msg.topic:
            self.process_pv_topic(self.pv_data, msg)
        elif "openWB/bat/" in msg.topic:
            self.process_bat_topic(self.bat_data, msg)
        elif "openWB/general/" in msg.topic:
            self.process_general_topic(self.general_data, msg)
        elif "openWB/graph/" in msg.topic:
            self.process_graph_topic(self.graph_data, msg)
        elif "openWB/optional/" in msg.topic:
            self.process_optional_topic(self.optional_data, msg)
        elif "openWB/counter/" in msg.topic:
            self.process_counter_topic(self.counter_data, msg)
        elif "openWB/system/" in msg.topic:
            self.process_system_topic(client, self.system_data, msg)
        elif "openWB/command/command_completed" == msg.topic:
            self.event_command_completed.set()
        else:
            log.warning("unknown subdata-topic: "+str(msg.topic))

    def set_json_payload(self, dict: Dict, msg: mqtt.MQTTMessage) -> None:
        """ dekodiert das JSON-Objekt und setzt diesen für den Value in das übergebene Dictionary, als Key wird der
        Name nach dem letzten / verwendet.

        Parameter
        ----------
        dict : dictionary
            Dictionary, in dem der Wert abgelegt wird
        msg :
            enthält den Payload als json-Objekt
        """
        try:
            regex = re.search("/([a-z,A-Z,0-9,_]+)(?!.*/)", msg.topic)
            if regex is None:
                raise Exception(f"Couldn't find key-name in {msg.topic}")
            key = regex.group(1)
            if msg.payload:
                dict[key] = decode_payload(msg.payload)
            else:
                if key in dict:
                    dict.pop(key)
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def set_json_payload_class(self, class_obj: Dict, msg: mqtt.MQTTMessage):
        """ dekodiert das JSON-Objekt und setzt diesen für den Value in das übergebene Dictionary, als Key wird der
        Name nach dem letzten / verwendet.

        Parameter
        ----------
        class_obj : dictionary
            Dictionary, in dem der Wert abgelegt wird
        msg :
            enthält den Payload als json-Objekt
        """
        try:
            regex = re.search("/([a-z,A-Z,0-9,_]+)(?!.*/)", msg.topic)
            if regex:
                key = regex.group(1)
                if msg.payload:
                    payload = decode_payload(msg.payload)
                    if isinstance(payload, Dict):
                        for key, value in payload.items():
                            setattr(class_obj, key, value)
                    else:
                        setattr(class_obj, key, decode_payload(msg.payload))
                else:
                    if isinstance(class_obj, Dict):
                        if key in class_obj:
                            class_obj.pop(key)
                    else:
                        log.error("Elemente können nur aus Dictionaries entfernt werden, nicht aus Klassen.")
            else:
                raise Exception(f"Key konnte nicht aus Topic {msg.topic} ermittelt werden.")
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_vehicle_topic(self, var: Dict[str, ev.Ev], msg: mqtt.MQTTMessage):
        """ Handler für die EV-Topics

        Parameter
        ----------
        var : Dictionary
            enthält aktuelle Daten
        msg :
            enthält Topic und Payload
        """
        try:
            index = get_index(msg.topic)
            if "openWB/vehicle/set/vehicle_update_completed" in msg.topic:
                self.event_vehicle_update_completed.set()
            elif re.search("/vehicle/[0-9]+/", msg.topic) is not None:
                if decode_payload(msg.payload) == "":
                    if re.search("/vehicle/[0-9]+/soc_module/config$", msg.topic) is not None:
                        var["ev"+index].soc_module = None
                    elif re.search("/vehicle/[0-9]+/get", msg.topic) is not None:
                        self.set_json_payload_class(var["ev"+index].data.get, msg)
                    else:
                        if "ev"+index in var:
                            var.pop("ev"+index)
                else:
                    if "ev"+index not in var:
                        var["ev"+index] = ev.Ev(int(index))

                    if re.search("/vehicle/[0-9]+/get", msg.topic) is not None:
                        self.set_json_payload_class(var["ev"+index].data.get, msg)
                    elif re.search("/vehicle/[0-9]+/set/ev_template$", msg.topic) is not None:
                        var["ev"+index].data.set.ev_template.data = dataclass_from_dict(
                            ev.EvTemplateData,
                            decode_payload(msg.payload))
                    elif re.search("/vehicle/[0-9]+/set", msg.topic) is not None:
                        self.set_json_payload_class(var["ev"+index].data.set, msg)
                    elif re.search("/vehicle/[0-9]+/soc_module/config$", msg.topic) is not None:
                        config = decode_payload(msg.payload)
                        if config["type"] is None:
                            var["ev"+index].soc_module = None
                        else:
                            mod = importlib.import_module(".vehicles."+config["type"]+".soc", "modules")
                            var["ev"+index].soc_module = mod.Soc(config, index)
                    elif re.search("/vehicle/[0-9]+/control_parameter/", msg.topic) is not None:
                        self.set_json_payload_class(
                            var["ev"+index].data.control_parameter, msg)
                    else:
                        self.set_json_payload_class(var["ev"+index].data, msg)
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_vehicle_charge_template_topic(self, var: Dict[str, ev.ChargeTemplate], msg: mqtt.MQTTMessage):
        """ Handler für die EV-Topics

        Parameter
        ----------
        var : Dictionary
            enthält aktuelle Daten
        msg :
            enthält Topic und Payload
        """
        try:
            index = get_index(msg.topic)
            if decode_payload(msg.payload) == "" and re.search("/vehicle/template/charge_template/[0-9]+$",
                                                               msg.topic) is not None:
                if "ct"+index in var:
                    var.pop("ct"+index)
            else:
                if "ct"+index not in var:
                    var["ct"+index] = ev.ChargeTemplate(int(index))
                if re.search("/vehicle/template/charge_template/[0-9]+/chargemode/scheduled_charging/plans/[0-9]+$",
                             msg.topic) is not None:
                    index_second = get_second_index(msg.topic)
                    if decode_payload(msg.payload) == "":
                        try:
                            var["ct"+index].data.chargemode.scheduled_charging.plans.pop(index_second)
                        except KeyError:
                            log.error("Es konnte kein Zielladen-Plan mit der ID " +
                                      str(index_second)+" in der Ladevorlage "+str(index)+" gefunden werden.")
                    else:
                        var["ct"+index].data.chargemode.scheduled_charging.plans[
                            index_second] = dataclass_from_dict(ev.ScheduledChargingPlan, decode_payload(msg.payload))
                elif re.search("/vehicle/template/charge_template/[0-9]+/time_charging/plans/[0-9]+$",
                               msg.topic) is not None:
                    index_second = get_second_index(msg.topic)
                    if decode_payload(msg.payload) == "":
                        try:
                            var["ct"+index].data.time_charging.plans.pop(index_second)
                        except KeyError:
                            log.error("Es konnte kein Zeitladen-Plan mit der ID " +
                                      str(index_second)+" in der Ladevorlage "+str(index)+" gefunden werden.")
                    else:
                        var["ct"+index].data.time_charging.plans[
                            index_second] = dataclass_from_dict(ev.TimeChargingPlan, decode_payload(msg.payload))
                else:
                    # Pläne unverändert übernehmen
                    scheduled_charging_plans = var["ct" + index].data.chargemode.scheduled_charging.plans
                    time_charging_plans = var["ct" + index].data.time_charging.plans
                    var["ct" + index].data = dataclass_from_dict(ev.ChargeTemplateData, decode_payload(msg.payload))
                    var["ct"+index].data.time_charging.plans = time_charging_plans
                    var["ct"+index].data.chargemode.scheduled_charging.plans = scheduled_charging_plans
                    self.event_charge_template.set()
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_vehicle_ev_template_topic(self, var: Dict[str, ev.EvTemplate], msg: mqtt.MQTTMessage):
        """ Handler für die EV-Topics

        Parameter
        ----------
        var : Dictionary
            enthält aktuelle Daten
        msg :
            enthält Topic und Payload
        """
        try:
            index = get_index(msg.topic)
            if re.search("/vehicle/template/ev_template/[0-9]+$", msg.topic) is not None:
                if decode_payload(msg.payload) == "":
                    if "et"+index in var:
                        var.pop("et"+index)
                else:
                    if "et"+index not in var:
                        var["et"+index] = ev.EvTemplate(et_num=int(index))
                    var["et" + index].data = dataclass_from_dict(ev.EvTemplateData, decode_payload(msg.payload))
                    self.event_ev_template.set()
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_chargepoint_topic(self, var: Dict[str, chargepoint.Chargepoint], msg: mqtt.MQTTMessage):
        """ Handler für die Ladepunkt-Topics

        Parameter
        ----------
        var : Dictionary
            enthält aktuelle Daten
        msg :
            enthält Topic und Payload
        """
        try:
            if re.search("/chargepoint/[0-9]+/", msg.topic) is not None:
                index = get_index(msg.topic)
                if decode_payload(msg.payload) == "":
                    if "cp"+index in var:
                        var.pop("cp"+index)
                else:
                    if "cp"+index not in var:
                        var["cp"+index] = chargepoint.ChargepointStateUpdate(
                            int(index),
                            self.event_copy_data,
                            self.event_global_data_initialized,
                            self.cp_template_data,
                            self.ev_data,
                            self.ev_charge_template_data,
                            self.ev_template_data)
                    if re.search("/chargepoint/[0-9]+/set/", msg.topic) is not None:
                        if re.search("/chargepoint/[0-9]+/set/log$", msg.topic) is not None:
                            var["cp"+index].chargepoint.data.set.log = dataclass_from_dict(
                                chargepoint.Log, decode_payload(msg.payload))
                        else:
                            self.set_json_payload_class(var["cp"+index].chargepoint.data.set, msg)
                    elif re.search("/chargepoint/[0-9]+/get/", msg.topic) is not None:
                        if re.search("/chargepoint/[0-9]+/get/connected_vehicle/", msg.topic) is not None:
                            self.set_json_payload_class(var["cp"+index].chargepoint.data.get.connected_vehicle, msg)
                        elif re.search("/chargepoint/[0-9]+/get/", msg.topic) is not None:
                            self.set_json_payload_class(var["cp"+index].chargepoint.data.get, msg)
                    elif re.search("/chargepoint/[0-9]+/config$", msg.topic) is not None:
                        config = json.loads(
                            str(msg.payload.decode("utf-8")))
                        if (var["cp"+index].chargepoint.chargepoint_module is None or
                                config["connection_module"] != var[
                                    "cp"+index].chargepoint.chargepoint_module.connection_module or
                                config["power_module"] != var["cp"+index].chargepoint.chargepoint_module.power_module):
                            mod = importlib.import_module(
                                ".chargepoints."+config["connection_module"]["type"]+".chargepoint_module", "modules")
                            var["cp"+index].chargepoint.chargepoint_module = mod.ChargepointModule(
                                config["id"], config["connection_module"], config["power_module"])
                        self.set_json_payload_class(var["cp"+index].chargepoint.data.config, msg)
                        self.event_cp_config.set()
            elif re.search("/chargepoint/get/", msg.topic) is not None:
                self.set_json_payload_class(self.cp_all_data.data.get, msg)
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_chargepoint_template_topic(self, var: Dict[str, chargepoint.CpTemplate], msg: mqtt.MQTTMessage):
        """ Handler für die Ladepunkt-Topics

        Parameter
        ----------
        var : Dictionary
            enthält aktuelle Daten
        msg :
            enthält Topic und Payload
        """
        try:
            index = get_index(msg.topic)
            payload = decode_payload(msg.payload)
            if re.search("/chargepoint/template/[0-9]+/autolock/", msg.topic) is not None:
                index_second = get_second_index(msg.topic)
                if payload == "":
                    var["cpt"+index].data.autolock.plans.pop(index_second)
                else:
                    var["cpt"+index].data.autolock.plans[
                        index_second] = dataclass_from_dict(AutolockPlan, payload)
            else:
                if payload == "":
                    var.pop("cpt"+index)
                else:
                    if "cpt"+index not in var:
                        var["cpt"+index] = chargepoint.CpTemplate()
                    autolock_plans = var["cpt"+index].data.autolock.plans
                    var["cpt"+index].data = dataclass_from_dict(chargepoint.CpTemplateData, payload)
                    var["cpt"+index].data.autolock.plans = autolock_plans
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_pv_topic(self, var: Dict[str, pv.Pv], msg: mqtt.MQTTMessage):
        """ Handler für die PV-Topics

        Parameter
        ----------
        var : Dictionary
            enthält aktuelle Daten
        msg :
            enthält Topic und Payload
        """
        try:
            if re.search("/pv/[0-9]+/", msg.topic) is not None:
                index = get_index(msg.topic)
                if decode_payload(msg.payload) == "":
                    if "pv"+index in var:
                        var.pop("pv"+index)
                else:
                    if "pv"+index not in var:
                        var["pv"+index] = pv.Pv(int(index))
                    if re.search("/pv/[0-9]+/config/", msg.topic) is not None:
                        self.set_json_payload_class(var["pv"+index].data.config, msg)
                    elif re.search("/pv/[0-9]+/get/", msg.topic) is not None:
                        self.set_json_payload_class(var["pv"+index].data.get, msg)
            elif re.search("/pv/", msg.topic) is not None:
                if re.search("/pv/config/", msg.topic) is not None:
                    self.set_json_payload_class(self.pv_all_data.data.config, msg)
                elif re.search("/pv/get/", msg.topic) is not None:
                    self.set_json_payload_class(self.pv_all_data.data.get, msg)
                elif re.search("/pv/set/", msg.topic) is not None:
                    self.set_json_payload_class(self.pv_all_data.data.set, msg)
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_bat_topic(self, var: Dict[str, bat.Bat], msg: mqtt.MQTTMessage):
        """ Handler für die Hausspeicher-Hardware_Topics

        Parameter
        ----------
        var : Dictionary
            enthält aktuelle Daten
        msg :
            enthält Topic und Payload
        """
        try:
            if re.search("/bat/[0-9]+/", msg.topic) is not None:
                index = get_index(msg.topic)
                if decode_payload(msg.payload) == "":
                    if "bat"+index in var:
                        var.pop("bat"+index)
                else:
                    if "bat"+index not in var:
                        var["bat"+index] = bat.Bat(int(index))
                    if re.search("/bat/[0-9]+/config$", msg.topic) is not None:
                        self.set_json_payload(var["bat"+index].data, msg)
                    elif re.search("/bat/[0-9]+/get/", msg.topic) is not None:
                        self.set_json_payload_class(var["bat"+index].data.get, msg)
                    elif re.search("/bat/[0-9]+/set/", msg.topic) is not None:
                        self.set_json_payload_class(var["bat"+index].data.set, msg)
            elif re.search("/bat/", msg.topic) is not None:
                if re.search("/bat/get/", msg.topic) is not None:
                    self.set_json_payload_class(self.bat_all_data.data.get, msg)
                elif re.search("/bat/set/", msg.topic) is not None:
                    self.set_json_payload_class(self.bat_all_data.data.set, msg)
                elif re.search("/bat/config/", msg.topic) is not None:
                    self.set_json_payload_class(self.bat_all_data.data.config, msg)
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_general_topic(self, var: general.General, msg: mqtt.MQTTMessage):
        """ Handler für die Allgemeinen-Topics

        Parameter
        ----------
        var : Dictionary
            enthält aktuelle Daten
        msg :
            enthält Topic und Payload
        """
        try:
            if re.search("/general/", msg.topic) is not None:
                if re.search("/general/ripple_control_receiver/", msg.topic) is not None:
                    self.set_json_payload_class(var.data.ripple_control_receiver, msg)
                elif re.search("/general/chargemode_config/", msg.topic) is not None:
                    if re.search("/general/chargemode_config/pv_charging/", msg.topic) is not None:
                        self.set_json_payload_class(var.data.chargemode_config.pv_charging, msg)
                    elif re.search("/general/chargemode_config/instant_charging/", msg.topic) is not None:
                        self.set_json_payload_class(var.data.chargemode_config.instant_charging, msg)
                    elif re.search("/general/chargemode_config/scheduled_charging/", msg.topic) is not None:
                        self.set_json_payload_class(var.data.chargemode_config.scheduled_charging, msg)
                    elif re.search("/general/chargemode_config/time_charging/", msg.topic) is not None:
                        self.set_json_payload_class(var.data.chargemode_config.time_charging, msg)
                    elif re.search("/general/chargemode_config/standby/", msg.topic) is not None:
                        self.set_json_payload_class(var.data.chargemode_config.standby, msg)
                    else:
                        self.set_json_payload_class(var.data.chargemode_config, msg)
                else:
                    self.set_json_payload_class(var.data, msg)
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_optional_topic(self, var: optional.Optional, msg: mqtt.MQTTMessage):
        """ Handler für die Optionalen-Topics

        Parameter
        ----------
        var : Dictionary
            enthält aktuelle Daten
        msg :
            enthält Topic und Payload
        """
        try:
            if re.search("/optional/", msg.topic) is not None:
                if re.search("/optional/led/", msg.topic) is not None:
                    self.set_json_payload_class(var.data.led, msg)
                elif re.search("/optional/rfid/", msg.topic) is not None:
                    self.set_json_payload_class(var.data.rfid, msg)
                elif re.search("/optional/int_display/", msg.topic) is not None:
                    self.set_json_payload_class(var.data.int_display, msg)
                elif re.search("/optional/et/", msg.topic) is not None:
                    if re.search("/optional/et/get/", msg.topic) is not None:
                        self.set_json_payload_class(var.data.et.get, msg)
                    elif re.search("/optional/et/config/", msg.topic) is not None:
                        self.set_json_payload_class(var.data.et.config, msg)
                    else:
                        self.set_json_payload_class(var.data.et, msg)
                else:
                    self.set_json_payload_class(var.data, msg)
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_counter_topic(self, var: Dict[str, counter.Counter], msg: mqtt.MQTTMessage):
        """ Handler für die Zähler-Topics

        Parameter
        ----------
        var : Dictionary
            enthält aktuelle Daten
        msg :
            enthält Topic und Payload
        """
        try:
            if re.search("/counter/[0-9]+/", msg.topic) is not None:
                index = get_index(msg.topic)
                if decode_payload(msg.payload) == "":
                    if "counter"+index in var:
                        var.pop("counter"+index)
                else:
                    if "counter"+index not in var:
                        var["counter"+index] = counter.Counter(int(index))
                    if re.search("/counter/[0-9]+/get", msg.topic) is not None:
                        self.set_json_payload_class(var["counter"+index].data.get, msg)
                    elif re.search("/counter/[0-9]+/set", msg.topic) is not None:
                        self.set_json_payload_class(var["counter"+index].data.set, msg)
                    elif re.search("/counter/[0-9]+/config/", msg.topic) is not None:
                        self.set_json_payload_class(var["counter"+index].data.config, msg)
            elif re.search("/counter/", msg.topic) is not None:
                if re.search("/counter/get", msg.topic) is not None:
                    self.set_json_payload_class(self.counter_all_data.data.get, msg)
                elif re.search("/counter/set", msg.topic) is not None:
                    self.set_json_payload_class(self.counter_all_data.data.set, msg)
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_system_topic(self, client: mqtt.Client, var: dict, msg: mqtt.MQTTMessage):
        """ Handler für die System-Topics

        Parameter
        ----------
        var : Dictionary
            enthält aktuelle Daten
        msg :
            enthält Topic und Payload
        """
        try:
            if "system" not in var:
                if decode_payload(msg.payload) == "":
                    if "system" in var:
                        var.pop("system")
                else:
                    var["system"] = system.System()
            if re.search("/device/[0-9]+/config$", msg.topic) is not None:
                index = get_index(msg.topic)
                if decode_payload(msg.payload) == "":
                    if "device"+index in var:
                        var.pop("device"+index)
                    else:
                        log.error("Es konnte kein Device mit der ID " +
                                  str(index)+" gefunden werden.")
                else:
                    device_config = decode_payload(msg.payload)
                    dev = importlib.import_module(".devices."+device_config["type"]+".device", "modules")
                    config = dataclass_from_dict(dev.device_descriptor.configuration_factory, device_config)
                    var["device"+index] = (dev.Device if hasattr(dev, "Device") else dev.create_device)(config)
                    # Durch das erneute Subscribe werden die Komponenten mit dem aktualisierten TCP-Client angelegt.
                    client.subscribe(f"openWB/system/device/{index}/component/+/config", 2)
            elif re.search("^.+/device/[0-9]+/component/[0-9]+/simulation$", msg.topic) is not None:
                index = get_index(msg.topic)
                index_second = get_second_index(msg.topic)
                var["device"+index].components["component"+index_second].sim_counter.data = dataclass_from_dict(
                    SimCounterState,
                    decode_payload(msg.payload))
            elif re.search("^.+/device/[0-9]+/component/[0-9]+/config$", msg.topic) is not None:
                index = get_index(msg.topic)
                index_second = get_second_index(msg.topic)
                if decode_payload(msg.payload) == "":
                    if "device"+index in var:
                        if "component"+str(index_second) in var["device"+index].components:
                            var["device"+index].components.pop(
                                "component"+str(index_second))
                            Pub().pub("openWB/system/device/"+str(index) +
                                      "/component/"+str(index_second), "")
                        else:
                            log.error("Es konnte keine Komponente mit der ID " +
                                      str(index_second)+" gefunden werden.")
                    else:
                        log.error("Es konnte kein Device mit der ID " +
                                  str(index)+" gefunden werden.")
                else:
                    # Es darf nicht einfach data["config"] aktualisiert werden, da in der __init__ auch die
                    # TCP-Verbindung aufgebaut wird, deren IP dann nicht aktualisiert werden würde.
                    component_config = decode_payload(msg.payload)
                    component = importlib.import_module(
                        f'.devices.{var["device"+index].device_config.type}.{component_config["type"]}', "modules")
                    config = dataclass_from_dict(component.component_descriptor.configuration_factory, component_config)
                    var["device"+index].add_component(config)
                    client.subscribe(f"openWB/system/device/{index}/component/{index_second}/simulation", 2)
            elif "mqtt" and "bridge" in msg.topic:
                index = get_index(msg.topic)
                parent_file = Path(__file__).resolve().parents[2]
                result = subprocess.run(
                    ["php", "-f", str(parent_file / "runs" / "savemqtt.php"), index, msg.payload],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                if len(result.stdout) > 0:
                    pub_system_message(msg.payload, result.stdout,
                                       MessageType.SUCCESS if result.returncode == 0 else MessageType.ERROR)
            # will be moved to separate handler!
            elif "GetRemoteSupport" in msg.topic:
                payload = decode_payload(msg.payload)
                splitted = payload.split(";")
                token = splitted[0]
                port = splitted[1] if len(splitted) > 1 else "2223"
                user = splitted[2] if len(splitted) > 2 else "getsupport"
                subprocess.run([str(Path(__file__).resolve().parents[2] / "runs" / "start_remote_support.sh"),
                                token, port, user])
            else:
                if "module_update_completed" in msg.topic:
                    self.event_module_update_completed.set()
                elif "openWB/system/available_branches" == msg.topic:
                    # Logged in update.log, not used in data.data and removed due to readability purposes of main.log.
                    return
                elif "openWB/system/subdata_initialized" == msg.topic:
                    if decode_payload(msg.payload) != "":
                        Pub().pub("openWB/system/subdata_initialized", "")
                        self.event_subdata_initialized.set()
                self.set_json_payload(var["system"].data, msg)
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_graph_topic(self, var: graph.Graph, msg: mqtt.MQTTMessage):
        """ Handler für die Graph-Topics

        Parameter
        ----------
        var : Dictionary
            enthält aktuelle Daten
        msg :
            enthält Topic und Payload
        """
        try:
            if re.search("/graph/config/", msg.topic) is not None:
                self.set_json_payload_class(var.data.config, msg)
        except Exception:
            log.exception("Fehler im subdata-Modul")
