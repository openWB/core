""" Modul, um die Daten vom Broker zu erhalten.
"""
import importlib
import logging
from pathlib import Path
from threading import Event
from typing import Dict, Union
import re
import subprocess
import paho.mqtt.client as mqtt

from control import bat_all, bat, counter, counter_all, general, io_device, optional, pv, pv_all
from control.chargepoint import chargepoint
from control.chargepoint.chargepoint_all import AllChargepoints
from control.chargepoint.chargepoint_data import Log
from control.chargepoint.chargepoint_state_update import ChargepointStateUpdate
from control.chargepoint.chargepoint_template import CpTemplate, CpTemplateData
from control.ev.charge_template import ChargeTemplate, ChargeTemplateData
from control.ev import ev
from control.ev.ev_template import EvTemplate, EvTemplateData
from control.limiting_value import LoadmanagementLimit
from control.optional_data import Ocpp
from helpermodules import graph, system
from helpermodules.broker import BrokerClient
from helpermodules.messaging import MessageType, pub_system_message
from helpermodules.utils import ProcessingCounter
from helpermodules.utils.run_command import run_command
from helpermodules.utils.topic_parser import decode_payload, get_index, get_second_index
from helpermodules.pub import Pub
from dataclass_utils import dataclass_from_dict
from modules.common.abstract_vehicle import CalculatedSocState, GeneralVehicleConfig
from modules.common.configurable_backup_cloud import ConfigurableBackupCloud
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
    io_actions = io_device.IoActions()
    io_states: Dict[str, io_device.IoStates] = {}
    optional_data = optional.Optional()
    system_data = {"system": system.System()}
    graph_data = graph.Graph()

    def __init__(self,
                 event_ev_template: Event,
                 event_cp_config: Event,
                 event_module_update_completed: Event,
                 event_copy_data: Event,
                 event_global_data_initialized: Event,
                 event_command_completed: Event,
                 event_subdata_initialized: Event,
                 event_vehicle_update_completed: Event,
                 event_start_internal_chargepoint: Event,
                 event_stop_internal_chargepoint: Event,
                 event_update_config_completed: Event,
                 event_update_soc: Event,
                 event_soc: Event,
                 event_jobs_running: Event,
                 event_modbus_server: Event,
                 event_restart_gpio: Event,):
        self.event_ev_template = event_ev_template
        self.event_cp_config = event_cp_config
        self.event_module_update_completed = event_module_update_completed
        self.event_copy_data = event_copy_data
        self.event_global_data_initialized = event_global_data_initialized
        self.event_command_completed = event_command_completed
        self.event_subdata_initialized = event_subdata_initialized
        self.event_vehicle_update_completed = event_vehicle_update_completed
        self.event_start_internal_chargepoint = event_start_internal_chargepoint
        self.event_stop_internal_chargepoint = event_stop_internal_chargepoint
        self.event_update_config_completed = event_update_config_completed
        self.event_update_soc = event_update_soc
        self.event_soc = event_soc
        self.event_jobs_running = event_jobs_running
        self.event_modbus_server = event_modbus_server
        self.event_restart_gpio = event_restart_gpio
        self.heartbeat = False
        # Immer wenn ein Subscribe hinzugefügt wird, wird der Zähler hinzugefügt und subdata_initialized gepublished.
        # Wenn subdata_initialized empfangen wird, wird der Zäheler runtergezählt. Erst wenn alle subdata_initialized
        # empfangen wurden, wurden auch die vorher subskribierten Topics empfangen und der Algorithmus kann starten.
        self.processing_counter = ProcessingCounter(self.event_subdata_initialized)

    def sub_topics(self):
        self.internal_broker_client = BrokerClient("mqttsub", self.on_connect, self.on_message)
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
            ("openWB/internal_io/#", 2),
            ("openWB/io/#", 2),
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
            ("openWB/system/io/#", 2),
            ("openWB/LegacySmartHome/Status/wattnichtHaus", 2),
        ])
        self.processing_counter.add_task()
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
        elif "openWB/io/action" in msg.topic:
            self.process_io_topic(self.io_actions, msg)
        elif "openWB/io/states" in msg.topic or "openWB/internal_io/states" in msg.topic:
            self.process_io_topic(self.io_states, msg)
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
        except AttributeError:
            pass
            # manche Topics werden nicht in einem Attribut gespeichert
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
                            self.processing_counter.add_task()
                            Pub().pub("openWB/system/subdata_initialized", True)
                        self.event_soc.set()
                    else:
                        # temporäres ChargeTemplate aktualisieren, wenn dem Fahrzeug ein anderes Ladeprofil zugeordnet
                        # wird
                        self.set_json_payload_class(var["ev"+index].data, msg)
                        if re.search("/vehicle/[0-9]+/charge_template$", msg.topic) is not None:
                            charge_template_id = int(decode_payload(msg.payload))
                            if var["ev"+index].data.charge_template != charge_template_id:
                                ev_id = get_index(msg.topic)
                                for cp in self.cp_data.values():
                                    if ((cp.chargepoint.data.set.charging_ev != -1 and
                                         cp.chargepoint.data.set.charging_ev == ev_id) or
                                            cp.chargepoint.data.config.ev == ev_id):
                                        cp.chargepoint.update_charge_template(
                                            self.ev_charge_template_data[f"ct{charge_template_id}"])
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_vehicle_charge_template_topic(self, var: Dict[str, ChargeTemplate], msg: mqtt.MQTTMessage):
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
            if re.search("/vehicle/template/charge_template/[0-9]+$", msg.topic) is not None:
                if decode_payload(msg.payload) == "":
                    if "ct"+index in var:
                        var.pop("ct"+index)
                if "ct"+index not in var:
                    var["ct"+index] = ChargeTemplate()
                var["ct"+index].data = dataclass_from_dict(ChargeTemplateData, decode_payload(msg.payload))
                # Temporäres ChargeTemplate aktualisieren, wenn persistentes geändert wird
                for vehicle in self.ev_data.values():
                    if vehicle.data.charge_template == int(index):
                        for cp in self.cp_data.values():
                            if ((cp.chargepoint.data.set.charging_ev != -1 and
                                    cp.chargepoint.data.set.charging_ev == vehicle.num) or
                                    cp.chargepoint.data.config.ev == vehicle.num):
                                # UI sendet immer alle Topics, auch nicht geänderte. Damit die temporären Topics nicht
                                # mehrfach gepbulished werden, muss das publishen der temporären Topics 1:1 erfolgen.
                                if re.search("/vehicle/template/charge_template/[0-9]+$", msg.topic) is not None:
                                    if decode_payload(msg.payload) == "":
                                        Pub().pub(f"openWB/chargepoint/{cp.chargepoint.num}/set/charge_template", "")
                                    else:
                                        cp.chargepoint.update_charge_template(var["ct"+index])
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
                        var["et"+index] = EvTemplate()
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
                    if re.search("/chargepoint/[0-9]+/config", msg.topic) is not None:
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
                        elif "charge_template" in msg.topic:
                            var["cp"+index].chargepoint.data.set.charge_template = ChargeTemplate()
                            var["cp"+index].chargepoint.data.set.charge_template.data = dataclass_from_dict(
                                ChargeTemplateData, decode_payload(msg.payload))
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
                        elif (re.search("/chargepoint/[0-9]+/get/error_timestamp$", msg.topic) is not None and
                              hasattr(var[f"cp{index}"].chargepoint.chargepoint_module, "client_error_context")):
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
                        if re.search("/chargepoint/[0-9]+/control_parameter/limit", msg.topic) is not None:
                            payload = decode_payload(msg.payload)
                            var["cp"+index].chargepoint.data.control_parameter.limit = dataclass_from_dict(
                                LoadmanagementLimit, payload)
                        else:
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
            if payload == "":
                var.pop("cpt"+index)
            else:
                if "cpt"+index not in var:
                    var["cpt"+index] = CpTemplate()
                var["cpt"+index].data = dataclass_from_dict(CpTemplateData, payload)
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
                if re.search("/general/prices/", msg.topic) is not None:
                    self.set_json_payload_class(var.data.prices, msg)
                elif re.search("/general/chargemode_config/", msg.topic) is not None:
                    if re.search("/general/chargemode_config/pv_charging/", msg.topic) is not None:
                        self.set_json_payload_class(var.data.chargemode_config.pv_charging, msg)
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

    def process_io_topic(self, var: Dict[str, Union[io_device.IoActions, io_device.IoStates]], msg: mqtt.MQTTMessage):
        """ Handler für die IO-Topics

        Parameter
        ----------
        var : Dictionary
            enthält aktuelle Daten
        msg :
            enthält Topic und Payload
        """
        try:
            if (re.search("/io/states/", msg.topic) is not None or
                    re.search("/internal_io/states/", msg.topic) is not None):
                if re.search("/io/states/[0-9]+/", msg.topic) is not None:
                    index = get_index(msg.topic)
                    key = "io_states"+index
                else:
                    index = "internal"
                    key = "internal_io_states"

                payload = decode_payload(msg.payload)
                if payload == "":
                    if key in var:
                        var.pop(key)
                else:
                    if key not in var:
                        var[key] = io_device.IoStates(index)
                if (re.search("/io/states/[0-9]+/get", msg.topic) is not None or
                        re.search("/internal_io/states/get", msg.topic) is not None):
                    # Sonst werden Dicts als Payload verwendet, aber es wird alles in ein eigenes Attribut gespeichert
                    # Typ ist hier auch kein typing.Dict, sondern ein generisches Dict[str, bool]
                    setattr(var[key].data.get, msg.topic.split("/")[-1], payload)
                elif (re.search("/io/states/[0-9]+/set", msg.topic) is not None or
                        re.search("/internal_io/states/set", msg.topic) is not None):
                    # Sonst werden Dicts als Payload verwendet, aber es wird alles in ein eigenes Attribut gespeichert
                    # Typ ist hier auch kein typing.Dict, sondern ein generisches Dict[str, bool]
                    setattr(var[key].data.set, msg.topic.split("/")[-1], payload)
                else:
                    self.set_json_payload_class(var[key].data, msg)
            elif "io/action" in msg.topic:
                if re.search("/io/action/[0-9]+/config", msg.topic) is not None:
                    index = get_index(msg.topic)
                    payload = decode_payload(msg.payload)
                    if payload == "":
                        if f"io_action{index}" in var.actions:
                            var.actions.pop(f"io_action{index}")
                    else:
                        mod = importlib.import_module(
                            f".io_actions.{payload['group']}.{payload['type']}.api", "modules")
                        config = dataclass_from_dict(mod.device_descriptor.configuration_factory, payload)
                        var.actions[f"io_action{index}"] = mod.create_action(config)
                elif re.search("/io/action/[0-9]+/timestamp", msg.topic) is not None:
                    index = get_index(msg.topic)
                    self.set_json_payload_class(var.actions[f"io_action{index}"], msg)
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
                        if config["type"] is None:
                            var.monitoring_stop()
                            var.monitoring_module = None
                        else:
                            mod = importlib.import_module(f".monitoring.{config['type']}.api", "modules")
                            config = dataclass_from_dict(mod.device_descriptor.configuration_factory, config)
                            var.monitoring_module = mod.create_monitoring(config)
                            var.monitoring_start()
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
                    client.subscribe(f"openWB/system/device/{index}/error_timestamp", 2)
                    self.processing_counter.add_task()
                    Pub().pub("openWB/system/subdata_initialized", True)
            elif re.search("^.+/device/[0-9]+/component/[0-9]+/simulation$", msg.topic) is not None:
                index = get_index(msg.topic)
                index_second = get_second_index(msg.topic)
                var["device"+index].components["component"+index_second].sim_counter.data = dataclass_from_dict(
                    SimCounterState,
                    decode_payload(msg.payload))
            elif re.search("^.+/device/[0-9]+/error_timestamp$", msg.topic) is not None:
                index = get_index(msg.topic)
                var["device"+index].client_error_context.error_timestamp = decode_payload(msg.payload)
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
                    self.processing_counter.add_task()
                    Pub().pub("openWB/system/subdata_initialized", True)
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
                if self.event_subdata_initialized.is_set():
                    Pub().pub("openWB/set/command/removeCloudBridge/todo",
                              {"command": "removeCloudBridge"})
                else:
                    log.debug("skipping data protection message on startup")
            elif re.search("^.+/io/[0-9]+/config$", msg.topic) is not None:
                index = get_index(msg.topic)
                if decode_payload(msg.payload) == "":
                    if "io"+index in var:
                        if var[f"io{index}"].config.configuration.host == "localhost":
                            var.pop("iolocal")
                        var.pop("io"+index)
                    else:
                        log.error("Es konnte kein IO-Device mit der ID " +
                                  str(index)+" gefunden werden.")
                else:
                    io_config = decode_payload(msg.payload)
                    if io_config["type"] == "add_on" and io_config["configuration"]["host"] == "localhost":
                        self.event_restart_gpio.set()
                        dev = importlib.import_module(f".internal_chargepoint_handler.{io_config['type']}.api",
                                                      "modules")
                        config = dataclass_from_dict(dev.device_descriptor.configuration_factory, io_config)
                        var["iolocal"] = dev.create_io(config)
                    dev = importlib.import_module(f".io_devices.{io_config['type']}.api",
                                                  "modules")
                    config = dataclass_from_dict(dev.device_descriptor.configuration_factory, io_config)
                    var["io"+index] = dev.create_io(config)
            elif re.search("^.+/io/[0-9]+/set/manual/analog_output", msg.topic) is not None:
                index = get_index(msg.topic)
                self.set_json_payload(var["io"+index].set_manual["analog_output"], msg)
            elif re.search("^.+/io/[0-9]+/set/manual/digital_output", msg.topic) is not None:
                index = get_index(msg.topic)
                self.set_json_payload(var["io"+index].set_manual["digital_output"], msg)
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
                        self.processing_counter.task_done()
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
