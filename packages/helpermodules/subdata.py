""" Modul, um die Daten vom Broker zu erhalten.
"""
import importlib
import logging
from pathlib import Path
import threading
from typing import Dict, Union
import re
import subprocess
import paho.mqtt.client as mqtt

from control import bat_all, bat, counter, counter_all, general, optional, pv, pv_all
from control.chargepoint import chargepoint
from control.chargepoint.chargepoint_all import AllChargepoints
from control.chargepoint.chargepoint_data import Log
from control.chargepoint.chargepoint_state_update import ChargepointStateUpdate
from control.chargepoint.chargepoint_template import CpTemplate, CpTemplateData
from control.ev.charge_template import ChargeTemplate, ChargeTemplateData
from control.ev import ev
from control.ev.ev_template import EvTemplate, EvTemplateData
from control.optional_data import Ocpp
from helpermodules import graph, system
from helpermodules.abstract_plans import AutolockPlan, ScheduledChargingPlan, TimeChargingPlan
from helpermodules.broker import InternalBrokerClient
from helpermodules.messaging import MessageType, pub_system_message
from helpermodules.utils.run_command import run_command
from helpermodules.utils.topic_parser import decode_payload, get_index, get_second_index
from helpermodules.pub import Pub
from dataclass_utils import dataclass_from_dict
from modules.common.abstract_vehicle import CalculatedSocState, GeneralVehicleConfig
from modules.common.configurable_backup_cloud import ConfigurableBackupCloud
from modules.common.configurable_ripple_control_receiver import ConfigurableRcr
from modules.common.configurable_tariff import ConfigurableElectricityTariff
from modules.common.simcount.simcounter_state import SimCounterState
from modules.internal_chargepoint_handler.internal_chargepoint_handler_config import (
    GlobalHandlerData, InternalChargepoint, RfidData)
from modules.vehicles.manual.config import ManualSoc

log = logging.getLogger(__name__)
mqtt_log = logging.getLogger("mqtt")


class SubData:
    """ Klasse, die die benötigten Topics abonniert, die Instanzen erstellt, wenn z.b. ein Modul neu konfiguriert
    wird, Instanzen löscht, wenn Module gelöscht werden, und die Werte in die Attribute der Instanzen schreibt.
    """

    # Instanzen
    cp_data: Dict[str, ChargepointStateUpdate] = {}
    cp_all_data = AllChargepoints()
    cp_template_data: Dict[str, CpTemplate] = {}
    pv_data: Dict[str, pv.Pv] = {}
    pv_all_data = pv_all.PvAll()
    ev_data: Dict[str, ev.Ev] = {}
    ev_template_data: Dict[str, EvTemplate] = {}
    ev_charge_template_data: Dict[str, ChargeTemplate] = {}
    counter_data: Dict[str, counter.Counter] = {}
    counter_all_data = counter_all.CounterAll()
    bat_all_data = bat_all.BatAll()
    bat_data: Dict[str, bat.Bat] = {}
    general_data = general.General()
    internal_chargepoint_data: Dict[str, Union[InternalChargepoint, GlobalHandlerData, RfidData]] = {
        "cp0": InternalChargepoint(),
        "cp1": InternalChargepoint(),
        "global_data": GlobalHandlerData(),
        "rfid_data": RfidData()}
    optional_data = optional.Optional()
    system_data = {"system": system.System()}
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
                 event_vehicle_update_completed: threading.Event,
                 event_scheduled_charging_plan: threading.Event,
                 event_time_charging_plan: threading.Event,
                 event_start_internal_chargepoint: threading.Event,
                 event_stop_internal_chargepoint: threading.Event,
                 event_update_config_completed: threading.Event,
                 event_update_soc: threading.Event,
                 event_soc: threading.Event,
                 event_jobs_running: threading.Event,
                 event_modbus_server: threading.Event,):
        self.event_ev_template = event_ev_template
        self.event_charge_template = event_charge_template
        self.event_cp_config = event_cp_config
        self.event_module_update_completed = event_module_update_completed
        self.event_copy_data = event_copy_data
        self.event_global_data_initialized = event_global_data_initialized
        self.event_command_completed = event_command_completed
        self.event_subdata_initialized = event_subdata_initialized
        self.event_vehicle_update_completed = event_vehicle_update_completed
        self.event_scheduled_charging_plan = event_scheduled_charging_plan
        self.event_time_charging_plan = event_time_charging_plan
        self.event_start_internal_chargepoint = event_start_internal_chargepoint
        self.event_stop_internal_chargepoint = event_stop_internal_chargepoint
        self.event_update_config_completed = event_update_config_completed
        self.event_update_soc = event_update_soc
        self.event_soc = event_soc
        self.event_jobs_running = event_jobs_running
        self.event_modbus_server = event_modbus_server
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
            ("openWB/vehicle/set/#", 2),
            ("openWB/vehicle/template/#", 2),
            ("openWB/vehicle/+/+", 2),
            ("openWB/vehicle/+/get/#", 2),
            ("openWB/vehicle/+/soc_module/config", 2),
            ("openWB/vehicle/+/set/#", 2),
            ("openWB/chargepoint/#", 2),
            ("openWB/pv/#", 2),
            ("openWB/bat/#", 2),
            ("openWB/general/#", 2),
            ("openWB/graph/#", 2),
            ("openWB/optional/#", 2),
            ("openWB/counter/#", 2),
            ("openWB/command/command_completed", 2),
            ("openWB/internal_chargepoint/#", 2),
            # MQTT Bridge Topics vor "openWB/system/+" abonnieren, damit sie auch vor
            # "openWB/system/subdata_initialized" empfangen werden!
            ("openWB/system/mqtt/bridge/+", 2),
            ("openWB/system/mqtt/+", 2),
            # Nicht mit hash # abonnieren, damit nicht die Komponenten vor den Devices empfangen werden!
            ("openWB/system/+", 2),
            ("openWB/system/backup_cloud/#", 2),
            ("openWB/system/device/module_update_completed", 2),
            ("openWB/system/device/+/config", 2),
            ("openWB/LegacySmartHome/Status/wattnichtHaus", 2),
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
            self.process_vehicle_topic(client, self.ev_data, msg)
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
        elif "openWB/internal_chargepoint/" in msg.topic:
            self.process_internal_chargepoint_topic(client, self.internal_chargepoint_data, msg)
        elif "openWB/optional/" in msg.topic:
            self.process_optional_topic(self.optional_data, msg)
        elif "openWB/counter/" in msg.topic:
            self.process_counter_topic(self.counter_data, msg)
        elif "openWB/system/" in msg.topic:
            self.process_system_topic(client, self.system_data, msg)
        elif "openWB/LegacySmartHome/" in msg.topic:
            self.process_legacy_smarthome_topic(client, self.counter_all_data, msg)
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

    def process_vehicle_topic(self, client: mqtt.Client, var: Dict[str, ev.Ev], msg: mqtt.MQTTMessage):
        """ Handler für die EV-Topics

        Parameter
        ----------
        var : Dictionary
            enthält aktuelle Daten
        msg :
            enthält Topic und Payload
        """
        try:
            if "openWB/vehicle/set/vehicle_update_completed" in msg.topic:
                self.event_vehicle_update_completed.set()
            elif re.search("/vehicle/[0-9]+/", msg.topic) is not None:
                index = get_index(msg.topic)
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
                        if (re.search("/vehicle/[0-9]+/get/force_soc_update", msg.topic) is not None and
                                decode_payload(msg.payload)):
                            self.event_update_soc.set()
                    elif re.search("/vehicle/[0-9]+/set", msg.topic) is not None:
                        self.set_json_payload_class(var["ev"+index].data.set, msg)
                    elif re.search("/vehicle/[0-9]+/soc_module/general_config", msg.topic) is not None:
                        var["ev"+index].soc_module.general_config = dataclass_from_dict(
                            GeneralVehicleConfig, decode_payload(msg.payload))
                    elif re.search("/vehicle/[0-9]+/soc_module/calculated_soc_state", msg.topic) is not None:
                        calculated_soc_state = dataclass_from_dict(CalculatedSocState, decode_payload(msg.payload))
                        if var["ev"+index].soc_module is not None:
                            if isinstance(var["ev"+index].soc_module.vehicle_config, ManualSoc):
                                if (calculated_soc_state.manual_soc and calculated_soc_state.manual_soc !=
                                        var["ev"+index].soc_module.calculated_soc_state.manual_soc):
                                    Pub().pub(f"openWB/vehicle/{index}/get/force_soc_update", True)
                            var["ev"+index].soc_module.calculated_soc_state = calculated_soc_state
                    elif re.search("/vehicle/[0-9]+/soc_module/config$", msg.topic) is not None:
                        config = decode_payload(msg.payload)
                        if config["type"] is None:
                            var["ev"+index].soc_module = None
                        else:
                            mod = importlib.import_module(".vehicles."+config["type"]+".soc", "modules")
                            config = dataclass_from_dict(mod.device_descriptor.configuration_factory, config)
                            var["ev"+index].soc_module = mod.create_vehicle(config, index)
                            client.subscribe(f"openWB/vehicle/{index}/soc_module/calculated_soc_state", 2)
                            client.subscribe(f"openWB/vehicle/{index}/soc_module/general_config", 2)
                        self.event_soc.set()
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
                                      str(index_second)+" in dem Lade-Profil "+str(index)+" gefunden werden.")
                    else:
                        var["ct"+index].data.chargemode.scheduled_charging.plans[
                            index_second] = dataclass_from_dict(ScheduledChargingPlan, decode_payload(msg.payload))
                    self.event_scheduled_charging_plan.set()
                elif re.search("/vehicle/template/charge_template/[0-9]+/time_charging/plans/[0-9]+$",
                               msg.topic) is not None:
                    index_second = get_second_index(msg.topic)
                    if decode_payload(msg.payload) == "":
                        try:
                            var["ct"+index].data.time_charging.plans.pop(index_second)
                        except KeyError:
                            log.error("Es konnte kein Zeitladen-Plan mit der ID " +
                                      str(index_second)+" in dem Lade-Profil "+str(index)+" gefunden werden.")
                    else:
                        var["ct"+index].data.time_charging.plans[
                            index_second] = dataclass_from_dict(TimeChargingPlan, decode_payload(msg.payload))
                    self.event_time_charging_plan.set()
                else:
                    # Pläne unverändert übernehmen
                    scheduled_charging_plans = var["ct" + index].data.chargemode.scheduled_charging.plans
                    time_charging_plans = var["ct" + index].data.time_charging.plans
                    var["ct" + index].data = dataclass_from_dict(ChargeTemplateData, decode_payload(msg.payload))
                    var["ct"+index].data.time_charging.plans = time_charging_plans
                    var["ct"+index].data.chargemode.scheduled_charging.plans = scheduled_charging_plans
                    self.event_charge_template.set()
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_vehicle_ev_template_topic(self, var: Dict[str, EvTemplate], msg: mqtt.MQTTMessage):
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
                        var["et"+index] = EvTemplate(et_num=int(index))
                    var["et" + index].data = dataclass_from_dict(EvTemplateData, decode_payload(msg.payload))
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
                    log.debug("Stop des Handlers für den internen Ladepunkt.")
                    self.event_stop_internal_chargepoint.set()
                    if "cp"+index in var:
                        var.pop("cp"+index)
                        self.set_internal_chargepoint_configured()
                else:
                    if "cp"+index not in var:
                        var["cp"+index] = ChargepointStateUpdate(
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
                                Log, decode_payload(msg.payload))
                        else:
                            self.set_json_payload_class(var["cp"+index].chargepoint.data.set, msg)
                    elif re.search("/chargepoint/[0-9]+/get/", msg.topic) is not None:
                        if re.search("/chargepoint/[0-9]+/get/connected_vehicle/", msg.topic) is not None:
                            self.set_json_payload_class(var["cp"+index].chargepoint.data.get.connected_vehicle, msg)
                        elif (re.search("/chargepoint/[0-9]+/get/soc$", msg.topic) is not None and
                              decode_payload(msg.payload) != var["cp"+index].chargepoint.data.get.soc):
                            # Wenn das Auto noch nicht zugeordnet ist, wird der SoC nach der Zuordnung aktualisiert
                            if var["cp"+index].chargepoint.data.set.charging_ev > -1:
                                Pub().pub(f'openWB/set/vehicle/{var["cp"+index].chargepoint.data.set.charging_ev}'
                                          '/get/force_soc_update', True)
                            self.set_json_payload_class(var["cp"+index].chargepoint.data.get, msg)
                        elif re.search("/chargepoint/[0-9]+/get/error_timestamp$", msg.topic) is not None:
                            var["cp" +
                                index].chargepoint.chargepoint_module.client_error_context.error_timestamp = (
                                decode_payload(msg.payload)
                            )
                            self.set_json_payload_class(var["cp"+index].chargepoint.data.get, msg)
                        elif re.search("/chargepoint/[0-9]+/get/simulation$", msg.topic) is not None:
                            var["cp"+index].chargepoint.chargepoint_module.sim_counter.data = dataclass_from_dict(
                                SimCounterState,
                                decode_payload(msg.payload))
                        else:
                            self.set_json_payload_class(var["cp"+index].chargepoint.data.get, msg)
                    elif re.search("/chargepoint/[0-9]+/config$", msg.topic) is not None:
                        self.process_chargepoint_config_topic(var, msg)
                    elif re.search("/chargepoint/[0-9]+/control_parameter/", msg.topic) is not None:
                        self.set_json_payload_class(var["cp"+index].chargepoint.data.control_parameter, msg)
            elif re.search("/chargepoint/get/", msg.topic) is not None:
                self.set_json_payload_class(self.cp_all_data.data.get, msg)
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_chargepoint_config_topic(self, var: Dict[str, chargepoint.CpTemplate], msg: mqtt.MQTTMessage):
        index = get_index(msg.topic)
        payload = decode_payload(msg.payload)
        if (var["cp"+index].chargepoint.chargepoint_module is None or
                payload != var["cp"+index].chargepoint.chargepoint_module.config):
            mod = importlib.import_module(
                ".chargepoints."+payload["type"]+".chargepoint_module", "modules")
            config = dataclass_from_dict(mod.chargepoint_descriptor.configuration_factory, payload)
            var["cp"+index].chargepoint.chargepoint_module = mod.ChargepointModule(config)
            self.set_internal_chargepoint_configured()
        if payload["type"] == "internal_openwb":
            log.debug("Neustart des Handlers für den internen Ladepunkt.")
            self.event_stop_internal_chargepoint.set()
            self.event_start_internal_chargepoint.set()
        self.set_json_payload_class(var["cp"+index].chargepoint.data.config, msg)
        self.event_cp_config.set()

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
                        var["cpt"+index] = CpTemplate()
                    autolock_plans = var["cpt"+index].data.autolock.plans
                    var["cpt"+index].data = dataclass_from_dict(CpTemplateData, payload)
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
                if re.search("/general/ripple_control_receiver/module", msg.topic) is not None:
                    config_dict = decode_payload(msg.payload)
                    if config_dict["type"] is None:
                        var.data.ripple_control_receiver.module = None
                        var.ripple_control_receiver = None
                    else:
                        mod = importlib.import_module(".ripple_control_receivers." +
                                                      config_dict["type"]+".ripple_control_receiver", "modules")
                        config = dataclass_from_dict(mod.device_descriptor.configuration_factory, config_dict)
                        var.data.ripple_control_receiver.module = config_dict
                        var.ripple_control_receiver = ConfigurableRcr(
                            config=config, component_initializer=mod.create_ripple_control_receiver)
                elif re.search("/general/ripple_control_receiver/get/", msg.topic) is not None:
                    self.set_json_payload_class(var.data.ripple_control_receiver.get, msg)
                elif re.search("/general/ripple_control_receiver/", msg.topic) is not None:
                    return
                elif re.search("/general/prices/", msg.topic) is not None:
                    self.set_json_payload_class(var.data.prices, msg)
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
                elif "openWB/general/extern" == msg.topic:
                    if decode_payload(msg.payload) is False:
                        self.event_jobs_running.set()
                    else:
                        # 5 Min Handler bis auf Heartbeat, Cleanup, ... beenden
                        self.event_jobs_running.clear()
                    self.set_json_payload_class(var.data, msg)
                    run_command([
                        str(Path(__file__).resolve().parents[2] / "runs" / "setup_network.sh")
                    ], process_exception=True)
                elif "openWB/general/modbus_control" == msg.topic:
                    if decode_payload(msg.payload) and self.general_data.data.extern:
                        self.event_modbus_server.set()
                elif "openWB/general/http_api" == msg.topic:
                    if (
                        self.event_subdata_initialized.is_set() and
                        self.general_data.data.http_api != decode_payload(msg.payload)
                    ):
                        pub_system_message(
                            msg.payload,
                            "Bitte die openWB <a href=\"/openWB/web/settings/#/System/SystemConfiguration\">"
                            "neu starten</a>, damit die Änderungen an der HTTP-API wirksam werden.",
                            MessageType.SUCCESS
                        )
                    self.set_json_payload_class(var.data, msg)
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
                elif re.search("/optional/ocpp/", msg.topic) is not None:
                    self.set_json_payload_class(var.data.ocpp, msg)
                elif re.search("/optional/int_display/", msg.topic) is not None:
                    self.set_json_payload_class(var.data.int_display, msg)
                    if re.search("/(standby|active|rotation)$", msg.topic) is not None:
                        # some topics require an update of the display manager or boot settings
                        run_command([
                            str(Path(__file__).resolve().parents[2] / "runs" / "update_local_display.sh")
                        ], process_exception=True)
                elif re.search("/optional/et/", msg.topic) is not None:
                    if re.search("/optional/et/get/prices", msg.topic) is not None:
                        var.data.et.get.prices = decode_payload(msg.payload)
                    elif re.search("/optional/et/get/", msg.topic) is not None:
                        self.set_json_payload_class(var.data.et.get, msg)
                    elif re.search("/optional/et/provider$", msg.topic) is not None:
                        config_dict = decode_payload(msg.payload)
                        if config_dict["type"] is None:
                            var.et_module = None
                        else:
                            mod = importlib.import_module(
                                f".electricity_tariffs.{config_dict['type']}.tariff", "modules")
                            config = dataclass_from_dict(mod.device_descriptor.configuration_factory, config_dict)
                            var.et_module = ConfigurableElectricityTariff(config, mod.create_electricity_tariff)
                            var.et_get_prices()
                    else:
                        self.set_json_payload_class(var.data.et, msg)
                elif re.search("/optional/ocpp/", msg.topic) is not None:
                    config_dict = decode_payload(msg.payload)
                    var.data.ocpp = dataclass_from_dict(Ocpp, config_dict)
                elif re.search("/optional/monitoring/", msg.topic) is not None:
                    # do not reconfigure monitoring if topic is received on startup
                    if self.event_subdata_initialized.is_set():
                        config = decode_payload(msg.payload)
                        if config["type"] is not None:
                            mod = importlib.import_module(f".monitoring.{config['type']}.api", "modules")
                            config = dataclass_from_dict(mod.device_descriptor.configuration_factory, config)
                            mod.create_config(config)
                            run_command(["sudo", "systemctl", "restart", "zabbix-agent2"], process_exception=True)
                            run_command(["sudo", "systemctl", "enable", "zabbix-agent2"], process_exception=True)
                        else:
                            run_command(["sudo", "systemctl", "stop", "zabbix-agent2"], process_exception=True)
                            run_command(["sudo", "systemctl", "disable", "zabbix-agent2"], process_exception=True)
                    else:
                        log.debug("skipping monitoring config on startup")
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
                if re.search("/counter/config", msg.topic) is not None:
                    self.set_json_payload_class(self.counter_all_data.data.config, msg)
                elif re.search("/counter/get", msg.topic) is not None:
                    self.set_json_payload_class(self.counter_all_data.data.get, msg)
                elif re.search("/counter/set/simulation", msg.topic) is not None:
                    self.counter_all_data.sim_counter.data = dataclass_from_dict(
                        SimCounterState,
                        decode_payload(msg.payload))
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
                    dev = importlib.import_module(f".devices.{device_config['vendor']}.{device_config['type']}.device",
                                                  "modules")
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
                    component = importlib.import_module(f'.devices.{var["device"+index].device_config.vendor}'
                                                        f'.{var["device"+index].device_config.type}'
                                                        f'.{component_config["type"]}',
                                                        "modules")
                    config = dataclass_from_dict(component.component_descriptor.configuration_factory, component_config)
                    var["device"+index].add_component(config)
                    client.subscribe(f"openWB/system/device/{index}/component/{index_second}/simulation", 2)
            elif "mqtt" and "bridge" in msg.topic:
                # do not reconfigure mqtt bridges if topic is received on startup
                if self.event_subdata_initialized.is_set():
                    index = get_index(msg.topic)
                    parent_file = Path(__file__).resolve().parents[2]
                    try:
                        result = run_command(
                            ["php", "-f", str(parent_file / "runs" / "save_mqtt.php"), index, msg.payload])
                        pub_system_message(msg.payload, result, MessageType.SUCCESS)
                    except subprocess.CalledProcessError as e:
                        log.debug(e.stdout)
                        pub_system_message(msg.payload, f'Fehler-Status: {e.returncode}<br />Meldung: {e.stderr}',
                                           MessageType.ERROR)
                else:
                    log.debug("skipping mqtt bridge message on startup")
            elif "mqtt" and "valid_partner_ids" in msg.topic:
                # duplicate topic for remote support service
                log.error(f"received valid partner ids: {decode_payload(msg.payload)}")
                Pub().pub("openWB-remote/valid_partner_ids", decode_payload(msg.payload))
            # will be moved to separate handler!
            elif "GetRemoteSupport" in msg.topic:
                log.warning("deprecated topic for remote support received!")
                payload = decode_payload(msg.payload)
                splitted = payload.split(";")
                token = splitted[0]
                port = splitted[1] if len(splitted) > 1 else "2223"
                user = splitted[2] if len(splitted) > 2 else "getsupport"
                run_command([str(Path(__file__).resolve().parents[2] / "runs" / "start_remote_support.sh"),
                             token, port, user], process_exception=True)
            elif "openWB/system/backup_cloud/config" in msg.topic:
                config_dict = decode_payload(msg.payload)
                if config_dict["type"] is None:
                    var["system"].backup_cloud = None
                else:
                    mod = importlib.import_module(".backup_clouds."+config_dict["type"]+".backup_cloud", "modules")
                    config = dataclass_from_dict(mod.device_descriptor.configuration_factory, config_dict)
                    var["system"].backup_cloud = ConfigurableBackupCloud(config, mod.create_backup_cloud)
            elif "openWB/system/backup_cloud/backup_before_update" in msg.topic:
                self.set_json_payload(var["system"].data["backup_cloud"], msg)
            elif ("openWB/system/dataprotection_acknowledged" == msg.topic and
                    decode_payload(msg.payload) is False):
                Pub().pub("openWB/set/command/removeCloudBridge/todo", {
                    "command": "removeCloudBridge"
                })
            else:
                if "module_update_completed" in msg.topic:
                    self.event_module_update_completed.set()
                elif ("openWB/system/available_branches" == msg.topic or
                      "openWB/system/time" == msg.topic):
                    # Logged in update.log, not used in data.data and removed due to readability purposes of main.log.
                    return
                elif "openWB/system/subdata_initialized" == msg.topic:
                    if decode_payload(msg.payload) != "":
                        Pub().pub("openWB/system/subdata_initialized", "")
                        self.event_subdata_initialized.set()
                elif "openWB/system/update_config_completed" == msg.topic:
                    if decode_payload(msg.payload) != "":
                        Pub().pub("openWB/system/update_config_completed", "")
                        self.event_update_config_completed.set()
                elif "openWB/system/debug_level" == msg.topic:
                    logging.getLogger().setLevel(decode_payload(msg.payload))
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

    def process_internal_chargepoint_topic(self, client: mqtt.Client, var: dict, msg: mqtt.MQTTMessage):
        try:
            if re.search("/internal_chargepoint/[0-1]/data/parent_cp", msg.topic) is not None:
                index = get_index(msg.topic)
                if decode_payload(msg.payload) != var[f"cp{index}"].data.parent_cp:
                    log.debug("Neustart des Handlers für den internen Ladepunkt.")
                    self.event_stop_internal_chargepoint.set()
                    self.event_start_internal_chargepoint.set()
                self.set_json_payload_class(var[f"cp{index}"].data, msg)
            elif re.search("/internal_chargepoint/[0-1]/", msg.topic) is not None:
                index = get_index(msg.topic)
                if re.search("/internal_chargepoint/[0-1]/data/", msg.topic) is not None:
                    self.set_json_payload_class(var[f"cp{index}"].data, msg)
                elif re.search("/internal_chargepoint/[0-1]/get/", msg.topic) is not None:
                    self.set_json_payload_class(var[f"cp{index}"].get, msg)
            elif "internal_chargepoint/global_data" in msg.topic:
                self.set_json_payload_class(var["global_data"], msg)
                if decode_payload(msg.payload)["parent_ip"] != var["global_data"].parent_ip:
                    log.debug("Neustart des Handlers für den internen Ladepunkt.")
                    self.event_stop_internal_chargepoint.set()
                    self.event_start_internal_chargepoint.set()
            elif "internal_chargepoint/last_tag" in msg.topic:
                self.set_json_payload_class(var["rfid_data"], msg)
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def set_internal_chargepoint_configured(self):
        for cp in self.cp_data.values():
            if cp.chargepoint.chargepoint_module.config.type == "internal_openwb":
                internal_configured = True
                break
        else:
            internal_configured = False
        self.internal_chargepoint_data["global_data"].configured = internal_configured

    def process_legacy_smarthome_topic(self, client: mqtt.Client, var: counter_all.CounterAll, msg: mqtt.MQTTMessage):
        """ Handler für die SmartHome-Topics des alten

        Parameter
        ----------
        var : Dictionary
            enthält aktuelle Daten
        msg :
            enthält Topic und Payload
        """
        try:
            if "openWB/LegacySmartHome/Status/wattnichtHaus" == msg.topic:
                # keine automatische Zuordnung, da das Topic anders heißt als der Wert in der Datenstruktur
                var.data.set.smarthome_power_excluded_from_home_consumption = decode_payload(msg.payload)
        except Exception:
            log.exception("Fehler im subdata-Modul")
