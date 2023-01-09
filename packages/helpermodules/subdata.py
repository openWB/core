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

from control import bat
from control import chargepoint
from control import counter
from control import counter_all
from control import ev
from control import general
from helpermodules import graph
from helpermodules.abstract_plans import AutolockPlan
from helpermodules.broker import InternalBrokerClient
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
    cp_data = {}
    cp_all_data = chargepoint.AllChargepoints()
    cp_template_data = {}
    pv_data = {}
    ev_data = {}
    ev_template_data = {}
    ev_charge_template_data = {}
    counter_data = {}
    counter_all_data = counter_all.CounterAll()
    bat_data = {}
    general_data = general.General()
    optional_data = optional.Optional()
    system_data = {}
    graph_data = {}

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

        self.bat_data["all"] = bat.BatAll()
        self.pv_data["all"] = pv.PvAll()
        self.graph_data["graph"] = graph.Graph()

    def sub_topics(self):
        self.internal_broker_client = InternalBrokerClient("mqttsub", self.on_connect, self.on_message)
        self.internal_broker_client.start_infinite_loop()

    def disconnect(self) -> None:
        self.internal_broker_client.disconnect()

    def on_connect(self, client, userdata, flags, rc):
        """ connect to broker and subscribe to set topics
        """
        client.subscribe("openWB/vehicle/#", 2)
        client.subscribe("openWB/chargepoint/#", 2)
        client.subscribe("openWB/pv/#", 2)
        client.subscribe("openWB/bat/#", 2)
        client.subscribe("openWB/general/#", 2)
        client.subscribe("openWB/graph/#", 2)
        client.subscribe("openWB/optional/#", 2)
        client.subscribe("openWB/counter/#", 2)
        client.subscribe("openWB/command/command_completed", 2)
        # Nicht mit wildcard abonnieren, damit nicht die Komponenten vor den Devices empfangen werden.
        client.subscribe("openWB/system/+", 2)
        client.subscribe("openWB/system/device/module_update_completed", 2)
        client.subscribe("openWB/system/mqtt/bridge/+", 2)
        client.subscribe("openWB/system/device/+/config", 2)
        Pub().pub("openWB/system/subdata_initialized", True)

    def on_message(self, client, userdata, msg):
        """ wartet auf eingehende Topics.
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

    def set_json_payload(self, dict: Dict, msg) -> None:
        """ dekodiert das JSON-Objekt und setzt diesen für den Value in das übergebene Dictionary, als Key wird der
        Name nach dem letzten / verwendet.

         Parameters
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

    def set_json_payload_class(self, class_obj, msg):
        """ dekodiert das JSON-Objekt und setzt diesen für den Value in das übergebene Dictionary, als Key wird der
        Name nach dem letzten / verwendet.
        Parameters
        ----------
        dict : dictionary
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

    def process_vehicle_topic(self, var, msg):
        """ Handler für die EV-Topics

         Parameters
        ----------
        client : (unused)
            vorgegebener Parameter
        userdata : (unused)
            vorgegebener Parameter
        msg:
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

    def process_vehicle_charge_template_topic(self, var, msg):
        """ Handler für die EV-Topics

         Parameters
        ----------
        client : (unused)
            vorgegebener Parameter
        userdata : (unused)
            vorgegebener Parameter
        msg:
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

    def process_vehicle_ev_template_topic(self, var, msg):
        """ Handler für die EV-Topics

         Parameters
        ----------
        client : (unused)
            vorgegebener Parameter
        userdata : (unused)
            vorgegebener Parameter
        msg:
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

    def process_chargepoint_topic(self, var, msg):
        """ Handler für die Ladepunkt-Topics

         Parameters
        ----------
        client : (unused)
            vorgegebener Parameter
        userdata : (unused)
            vorgegebener Parameter
        msg:
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

    def process_chargepoint_template_topic(self, var, msg):
        """ Handler für die Ladepunkt-Topics

         Parameters
        ----------
        client : (unused)
            vorgegebener Parameter
        userdata : (unused)
            vorgegebener Parameter
        msg:
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

    def process_pv_topic(self, var, msg):
        """ Handler für die PV-Topics

         Parameters
        ----------
        client : (unused)
            vorgegebener Parameter
        userdata : (unused)
            vorgegebener Parameter
        msg:
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
                        self.set_json_payload(var["pv"+index].data["config"], msg)
                    elif re.search("/pv/[0-9]+/get/", msg.topic) is not None:
                        self.set_json_payload(var["pv"+index].data["get"], msg)
            elif re.search("/pv/", msg.topic) is not None:
                if re.search("/pv/config/", msg.topic) is not None:
                    if "config" not in var["all"].data:
                        var["all"].data["config"] = {}
                    self.set_json_payload(var["all"].data["config"], msg)
                elif re.search("/pv/get/", msg.topic) is not None:
                    if "get" not in var["all"].data:
                        var["all"].data["get"] = {}
                    self.set_json_payload(var["all"].data["get"], msg)
                elif re.search("/pv/set/", msg.topic) is not None:
                    if "set" not in var["all"].data:
                        var["all"].data["set"] = {}
                    self.set_json_payload(var["all"].data["set"], msg)
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_bat_topic(self, var, msg):
        """ Handler für die Hausspeicher-Hardware_Topics

         Parameters
        ----------
        client : (unused)
            vorgegebener Parameter
        userdata : (unused)
            vorgegebener Parameter
        msg:
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
                        if "get" not in var["bat"+index].data:
                            var["bat"+index].data["get"] = {}
                        self.set_json_payload(var["bat"+index].data["get"], msg)
                    elif re.search("/bat/[0-9]+/set/", msg.topic) is not None:
                        if "set" not in var["bat"+index].data:
                            var["bat"+index].data["set"] = {}
                        self.set_json_payload(var["bat"+index].data["set"], msg)
            elif re.search("/bat/", msg.topic) is not None:
                if re.search("/bat/get/", msg.topic) is not None:
                    if "get" not in var["all"].data:
                        var["all"].data["get"] = {}
                    self.set_json_payload(var["all"].data["get"], msg)
                elif re.search("/bat/set/", msg.topic) is not None:
                    if "set" not in var["all"].data:
                        var["all"].data["set"] = {}
                    self.set_json_payload(var["all"].data["set"], msg)
                elif re.search("/bat/config/", msg.topic) is not None:
                    if "config" not in var["all"].data:
                        var["all"].data["config"] = {}
                    self.set_json_payload(var["all"].data["config"], msg)
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_general_topic(self, var, msg):
        """ Handler für die Allgemeinen-Topics

         Parameters
        ----------
        client : (unused)
            vorgegebener Parameter
        userdata : (unused)
            vorgegebener Parameter
        msg:
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

    def process_optional_topic(self, var, msg):
        """ Handler für die Optionalen-Topics

         Parameters
        ----------
        client : (unused)
            vorgegebener Parameter
        userdata : (unused)
            vorgegebener Parameter
        msg:
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

    def process_counter_topic(self, var, msg):
        """ Handler für die Zähler-Topics

         Parameters
        ----------
        client : (unused)
            vorgegebener Parameter
        userdata : (unused)
            vorgegebener Parameter
        msg:
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
                        if "get" not in var["counter"+index].data:
                            var["counter"+index].data["get"] = {}
                        self.set_json_payload(
                            var["counter"+index].data["get"], msg)
                    elif re.search("/counter/[0-9]+/set", msg.topic) is not None:
                        if "set" not in var["counter"+index].data:
                            var["counter"+index].data["set"] = {}
                        self.set_json_payload(
                            var["counter"+index].data["set"], msg)
                    elif re.search("/counter/[0-9]+/config/", msg.topic) is not None:
                        if "config" not in var["counter"+index].data:
                            var["counter"+index].data["config"] = {}
                        self.set_json_payload(
                            var["counter"+index].data["config"], msg)
            elif re.search("/counter/", msg.topic) is not None:
                if re.search("/counter/get", msg.topic) is not None:
                    self.set_json_payload_class(self.counter_all_data.data.get, msg)
                elif re.search("/counter/set", msg.topic) is not None:
                    self.set_json_payload_class(self.counter_all_data.data.set, msg)
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_system_topic(self, client, var, msg):
        """Handler für die System-Topics

         Parameters
        ----------
        client : (unused)
            vorgegebener Parameter
        userdata : (unused)
            vorgegebener Parameter
        msg:
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
            elif re.search("/device/[0-9]+/get$", msg.topic) is not None:
                index = get_index(msg.topic)
                if "get" not in var["device"+index].data:
                    var["device"+index].data["get"] = {}
                self.set_json_payload(var["device"+index].data["get"], msg)
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
                subprocess.call(["php", "-f", str(parent_file / "runs" / "savemqtt.php"), index, msg.payload])
            elif "GetRemoteSupport" in msg.topic:
                payload = decode_payload(msg.payload)
                splitted = payload.split(";")
                token = splitted[0]
                port = splitted[1]
                if len(splitted) == 3:
                    user = splitted[2]
                else:
                    user = "getsupport"
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

    def process_graph_topic(self, var, msg):
        """ Handler für die Graph-Topics

         Parameters
        ----------
        client : (unused)
            vorgegebener Parameter
        userdata : (unused)
            vorgegebener Parameter
        msg:
            enthält Topic und Payload
        """
        try:
            if re.search("/graph/", msg.topic) is not None:
                if re.search("/graph/config/", msg.topic) is not None:
                    if "config" not in var["graph"].data:
                        var["graph"].data["config"] = {}
                    self.set_json_payload(var["graph"].data["config"], msg)
        except Exception:
            log.exception("Fehler im subdata-Modul")
