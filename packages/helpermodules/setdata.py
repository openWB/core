""" Modul, um die Daten vom Broker zu erhalten.
"""

import copy
import dataclasses
import threading
from typing import List, Optional, Tuple
import re
import paho.mqtt.client as mqtt

import logging
from helpermodules import subdata
from helpermodules.broker import InternalBrokerClient
from helpermodules.pub import Pub
from helpermodules.utils.topic_parser import decode_payload, get_index
from helpermodules.update_config import UpdateConfig
import dataclass_utils

log = logging.getLogger(__name__)
mqtt_log = logging.getLogger("mqtt")


class SetData:
    def __init__(self,
                 event_ev_template: threading.Event,
                 event_charge_template: threading.Event,
                 event_cp_config: threading.Event,
                 event_subdata_initialized: threading.Event):
        self.event_ev_template = event_ev_template
        self.event_charge_template = event_charge_template
        self.event_cp_config = event_cp_config
        self.event_subdata_initialized = event_subdata_initialized
        self.heartbeat = False

    def set_data(self):
        self.internal_broker_client = InternalBrokerClient("mqttset", self.on_connect, self.on_message)
        self.event_subdata_initialized.wait()
        log.debug("Subdata initialization completed. Starting setdata loop to broker.")
        self.internal_broker_client.start_infinite_loop()

    def disconnect(self) -> None:
        self.internal_broker_client.disconnect()

    def on_connect(self, client: mqtt.Client, userdata, flags: dict, rc: int):
        """ connect to broker and subscribe to set topics
        """
        client.subscribe("openWB/set/#", 2)

    def on_message(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
        """ ruft die Funktion auf, um das Topic zu verarbeiten. Wenn die Topics mit Locking verarbeitet werden,
        wird gewartet, bis das Locking aufgehoben wird.

        Parameters
        ----------
        client : (unused)
            vorgegebener Parameter
        userdata : (unused)
            vorgegebener Parameter
        msg:
            enthält Topic und Payload
        """
        self.heartbeat = True
        if decode_payload(msg.payload) != "":
            mqtt_log.debug(f"Topic: {msg.topic}, Payload: {decode_payload(msg.payload)}")
            if "openWB/set/vehicle/" in msg.topic:
                if "openWB/set/vehicle/template/ev_template/" in msg.topic:
                    self.event_ev_template.wait(5)
                elif "openWB/set/vehicle/template/charge_template/" in msg.topic:
                    self.event_charge_template.wait(5)
                self.process_vehicle_topic(msg)
            elif "openWB/set/chargepoint/" in msg.topic:
                self.process_chargepoint_topic(msg)
            elif "openWB/set/pv/" in msg.topic:
                self.process_pv_topic(msg)
            elif "openWB/set/bat/" in msg.topic:
                self.process_bat_topic(msg)
            elif "openWB/set/general/" in msg.topic:
                self.process_general_topic(msg)
            elif "openWB/set/optional/" in msg.topic:
                self.process_optional_topic(msg)
            elif "openWB/set/counter/" in msg.topic:
                self.process_counter_topic(msg)
            elif "openWB/set/log/" in msg.topic:
                self.process_log_topic(msg)
            elif "openWB/set/graph/" in msg.topic:
                self.process_graph_topic(msg)
            elif "openWB/set/system/" in msg.topic:
                self.process_system_topic(msg)
            elif "openWB/set/command/" in msg.topic:
                self.process_command_topic(msg)

    def _validate_value(self, msg: mqtt.MQTTMessage, data_type, ranges=[], collection=None, pub_json=False,
                        retain: bool = True):
        """ prüft, ob der Wert vom angegebenen Typ ist.

        Parameter
        ---------
        msg:
            Broker-Nachricht
        data_type: float, int, str, "json", None, bool
            Datentyp (None für komplexe Datenstrukturen, wie z.B. Hierarchie)
        ranges: [(int/float/None, int/float/None), ..]
            Liste mit Tuples, die die Wertebereiche enthalten (None für unendlich)
        collection = list/dict
            Angabe, ob und welche Kollektion erwartet wird
        pub_json : true/false
            gibt an, ob das Topic von openWB/set/.. an openWB/.. veröffentlicht werden soll oder ein json-Objekt,
            dass mehrere Daten enthält.
        """
        valid = False
        try:
            value = decode_payload(msg.payload)
            if data_type is None or data_type == "json":
                # Wenn kein gültiges json-Objekt übergeben worden wäre, wäre bei loads eine Exception aufgetreten.
                valid = True
            elif collection is not None:
                if self._validate_collection_value(msg, data_type, ranges, collection):
                    valid = True
            elif data_type == str:
                if isinstance(value, str) or value is None:
                    valid = True
                else:
                    log.error(f"Payload ungültig: Topic {msg.topic}, Payload {value} sollte ein String sein.")
            elif data_type == int or data_type == float:
                if self._validate_min_max_value(value, msg, data_type, ranges):
                    valid = True
            elif data_type == bool:
                valid, value = self._validate_bool_value(value, msg)

            if valid:
                if not pub_json:
                    Pub().pub(msg.topic.replace('set/', '', 1), value, retain=retain)
                    Pub().pub(msg.topic, "")
                else:
                    # aktuelles json-Objekt liegt in subdata
                    index = get_index(msg.topic)
                    if "charge_template" in msg.topic:
                        event = self.event_charge_template
                        if "ct"+str(index) in subdata.SubData.ev_charge_template_data:
                            template = dataclass_utils.asdict(copy.deepcopy(
                                subdata.SubData.ev_charge_template_data["ct"+str(index)].data))
                            # Wenn eine Einzeleinstellung empfangen wird, muss das gesamte Template veröffentlicht
                            # werden (pub_json=True), allerdings ohne Pläne. Diese sind in einem Extra-Topic und werden
                            # immer als komplettes json empfangen (mit pub_json=False).
                            try:
                                template["chargemode"]["scheduled_charging"].pop("plans")
                            except KeyError:
                                log.debug("Key 'plans' nicht gefunden, keine Zielladen-Pläne vorhanden.")
                            try:
                                template["time_charging"].pop("plans")
                            except KeyError:
                                log.debug("Key 'plans' nicht gefunden, keine Zeitladen-Pläne vorhanden.")
                        else:
                            template = {}
                    elif "ev_template" in msg.topic:
                        event = self.event_ev_template
                        if "et"+str(index) in subdata.SubData.ev_template_data:
                            template = copy.deepcopy(
                                subdata.SubData.ev_template_data["et"+str(index)].data)
                        else:
                            template = {}
                    elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/config.*$", msg.topic) is not None:
                        event = self.event_cp_config
                        if "cp"+str(index) in subdata.SubData.cp_data:
                            template = dataclasses.asdict(
                                subdata.SubData.cp_data["cp"+str(index)].chargepoint.data.config)
                        else:
                            template = {}
                    else:
                        raise ValueError("Zu "+msg.topic+" konnte kein passendes json-Objekt gefunden werden.")
                    # Wert, der aktualisiert werden soll, erstellen/finden und updaten
                    if event == self.event_cp_config:
                        key_list = msg.topic.split("/")[5:]
                    else:
                        key_list = msg.topic.split("/")[6:]
                    self._change_key(template, key_list, value)
                    # publish
                    regex = re.search('(?!/)([0-9]*)(?=/|$)', msg.topic)
                    if regex is None:
                        raise Exception(f"Couldn't find index in {msg.topic}")
                    index_pos = regex.end()
                    if event == self.event_cp_config:
                        topic = msg.topic[:index_pos]+"/config"
                    else:
                        topic = msg.topic[:index_pos]
                    topic = topic.replace('set/', '', 1)
                    Pub().pub(topic, template, retain=retain)
                    Pub().pub(msg.topic, "")
                    event.clear()
            else:
                Pub().pub(msg.topic, "")
        except Exception:
            log.exception(f"Fehler im setdata-Modul: Topic {msg.topic}, Value: {msg.payload}")
            Pub().pub(msg.topic, "")

    def _change_key(self, next_level, key_list, value):
        """ rekursive Funktion, die den Eintrag im entsprechenden Dictionary aktualisiert oder anlegt.

        Parameter
        ---------
        next_level: dict
            Beim ersten Aufruf: Dictionary, das aktualisiert werden soll.
            Danach: Dictionary aus den verschachtelten Dictionaries, das gerade betrachtet werden soll.
        key_list: list
            Liste der Keys aus den verschachtelten Dictionaries, unter denen der Eintrag zu finden ist.
        value:
            Wert, der geschrieben werden soll.
        """
        if len(key_list) == 1:
            next_level[key_list[0]] = value
        else:
            if key_list[0] not in next_level:
                next_level[key_list[0]] = {}
            next_key = key_list[0]
            key_list.pop(0)
            self._change_key(next_level[next_key], key_list, value)

    def _validate_collection_value(self, msg: mqtt.MQTTMessage, data_type, ranges=None, collection=None):
        """ prüft, ob die Liste vom angegebenen Typ ist und ob Minimal- und Maximalwert eingehalten werden.

        Parameter
        ---------
        msg:
            Broker-Nachricht
        data_type: float, int
            Datentyp, den die Liste enthalten soll
        min_value: int/float
            Minimalwert, den die Elemente in der Liste nicht unterschreiten dürfen
        max_value= int/float
            Maximalwert, den die Elemente in der Liste nicht überschreiten dürfen
        collection = list/dict
            Angabe, ob und welche Kollektion erwartet wird
        """
        try:
            valid = False
            value = decode_payload(msg.payload)
            if isinstance(value, list):
                for item in value:
                    if not self._validate_min_max_value(item, msg, data_type, ranges):
                        break
                else:
                    valid = True
            elif isinstance(value, dict):
                for item in value.values():
                    if not self._validate_min_max_value(item, msg, data_type, ranges):
                        break
                else:
                    valid = True
            else:
                log.error("Payload ungültig: Topic "+str(msg.topic)+", Payload " +
                          str(value)+" sollte eine Kollektion vom Typ "+str(collection)+" sein.")
            return valid
        except Exception:
            log.exception(f"Fehler im setdata-Modul: Topic {msg.topic}, Value: {msg.payload}")

    def _validate_min_max_value(self, value, msg: mqtt.MQTTMessage, data_type,
                                ranges: Optional[List[Tuple[int, float]]] = None):
        """ prüft, ob der Payload Minimal- und Maximalwert einhält.

        Parameter
        ---------
        value: int/float
            dekodierter Payload
        msg:
            Broker-Nachricht
        data_type: float, int
            Datentyp
        min_value: int/float
            Minimalwert
        max_value= int/float
            Maximalwert
        """
        try:
            valid = True
            # Wenn ein Float erwartet wird, kann auch ein Int akzeptiert werden, da dies automatisch umgewandelt
            # wird, falls erforderlich.
            if isinstance(value, data_type) or (data_type == float and isinstance(value, int)):
                if ranges:
                    for range in ranges:
                        if range[0] is not None and range[1] is not None:
                            if range[0] <= value <= range[1]:
                                break
                        elif range[0] is not None:
                            if value >= range[0]:
                                break
                        elif range[1] is not None:
                            if value <= range[1]:
                                break
                    else:
                        log.error("Payload ungültig: Topic "+str(msg.topic)+", Payload " +
                                  str(value)+" liegt in keinem der angegebenen Wertebereiche.")
                        valid = False
            elif value is None:
                if ranges:
                    for range in ranges:
                        if range[0] is None and range[1] is None:
                            break
                    else:
                        log.error("Payload ungültig: Topic "+str(msg.topic) +
                                  ", Payload "+str(value)+" darf nicht 'None' sein.")
                        valid = False
                else:
                    log.error("Payload ungültig: Topic "+str(msg.topic) +
                              ", Payload "+str(value)+" darf nicht 'None' sein.")
                    valid = False
            else:
                if data_type == int:
                    log.error("Payload ungültig: Topic "+str(msg.topic) +
                              ", Payload "+str(value)+" sollte ein Int sein.")
                elif data_type == float:
                    log.error("Payload ungültig: Topic "+str(msg.topic) +
                              ", Payload "+str(value)+" sollte ein Float sein.")
                valid = False
            return valid
        except Exception:
            log.exception(f"Fehler im setdata-Modul: Topic {msg.topic}, Value: {msg.payload}")

    def _validate_bool_value(self, value, msg: mqtt.MQTTMessage):
        if isinstance(value, bool):
            return True, value
        else:
            if value == 0 or value == 1:
                return True, bool(value)
            else:
                log.error(f"Payload ungültig: Topic {msg.topic}, Payload {value} sollte ein Boolean oder 0/1 sein.")
                return False, value

    def __unknown_topic(self, msg: mqtt.MQTTMessage) -> None:
        try:
            if msg.payload:
                log.error(f"Unbekanntes set-Topic: {msg.topic}, {decode_payload(msg.payload)}")
                Pub().pub(msg.topic, "")
            else:
                log.error("Unbekanntes set-Topic: " +
                          str(msg.topic)+" mit leerem Payload")
                Pub().pub(msg.topic, "")
        except Exception:
            log.exception(f"Fehler im setdata-Modul: Topic {msg.topic}, Value: {msg.payload}")

    def process_vehicle_topic(self, msg: mqtt.MQTTMessage):
        """ Handler für die EV-Topics

         Parameters
        ----------
        msg:
            enthält Topic und Payload
        """
        try:
            if "/name" in msg.topic:
                self._validate_value(msg, str)
            elif "openWB/set/vehicle/template" in msg.topic:
                self._subprocess_vehicle_chargemode_topic(msg)
            elif "openWB/set/vehicle/set/vehicle_update_completed" in msg.topic:
                self._validate_value(msg, bool)
            elif "/set/soc_error_counter" in msg.topic:
                self._validate_value(msg, int, [(0, float("inf"))])
            elif "/soc_module/config" in msg.topic:
                self._validate_value(msg, "json")
            elif "/get/fault_state" in msg.topic:
                self._validate_value(msg, int, [(0, 2)])
            elif "/get/fault_str" in msg.topic:
                self._validate_value(msg, str)
            elif "/tag_id" in msg.topic:
                self._validate_value(msg, str, collection=list)
            elif "/set/ev_template" in msg.topic:
                self._validate_value(msg, "json")
            elif ("/charge_template" in msg.topic or
                    "/ev_template" in msg.topic):
                self._validate_value(msg, int, [(0, float("inf"))])
            elif "/get/soc_timestamp" in msg.topic:
                self._validate_value(msg, str)
            elif "/get/soc" in msg.topic:
                self._validate_value(msg, float, [(0, 100)])
            elif "/get/range" in msg.topic:
                self._validate_value(msg, float, [(0, 1000)])
            elif "/get/force_soc_update" in msg.topic:
                self._validate_value(msg, bool)
            elif "/control_parameter/required_current" in msg.topic:
                self._validate_value(msg, float, [(6, 32), (0, 0)])
            elif "/control_parameter/phases" in msg.topic:
                self._validate_value(msg, int, [(0, 3)])
            elif ("/control_parameter/submode" in msg.topic or
                    "/control_parameter/chargemode" in msg.topic):
                self._validate_value(msg, str)
            elif "/control_parameter/prio" in msg.topic:
                self._validate_value(msg, bool)
            elif ("/control_parameter/timestamp_switch_on_off" in msg.topic or
                    "/control_parameter/timestamp_auto_phase_switch" in msg.topic or
                    "/control_parameter/timestamp_perform_phase_switch" in msg.topic or
                    "/control_parameter/current_plan" in msg.topic):
                self._validate_value(msg, str)
            elif ("/control_parameter/used_amount_instant_charging" in msg.topic or
                    "/control_parameter/imported_at_plan_start" in msg.topic):
                self._validate_value(msg, float, [(0, float("inf"))])
            else:
                self.__unknown_topic(msg)
        except Exception:
            log.exception(f"Fehler im setdata-Modul: Topic {msg.topic}, Value: {msg.payload}")

    def _subprocess_vehicle_chargemode_topic(self, msg: mqtt.MQTTMessage):
        """ Handler für die EV-Chargemode-Template-Topics
        Parameters
        ----------
        msg:
            enthält Topic und Payload
        """
        try:
            if "charge_template" in msg.topic:
                if "/name" in msg.topic:
                    self._validate_value(msg, str, pub_json=True)
                elif ("/load_default" in msg.topic or
                        "/disable_after_unplug" in msg.topic or
                        "/prio" in msg.topic):
                    self._validate_value(msg, bool, pub_json=True)
                elif "/chargemode/selected" in msg.topic:
                    self._validate_value(msg, str, pub_json=True)
                elif "/chargemode/instant_charging/current" in msg.topic:
                    self._validate_value(msg, int, [(6, 32)], pub_json=True)
                elif "/chargemode/instant_charging/limit/selected" in msg.topic:
                    self._validate_value(msg, str, pub_json=True)
                elif "/chargemode/instant_charging/limit/soc" in msg.topic:
                    self._validate_value(msg, int, [(0, 100)], pub_json=True)
                elif "/chargemode/instant_charging/limit/amount" in msg.topic:
                    self._validate_value(msg, int, [(1000, float("inf"))], pub_json=True)
                elif "/chargemode/pv_charging/feed_in_limit" in msg.topic:
                    self._validate_value(msg, bool, pub_json=True)
                elif "/chargemode/pv_charging/min_current" in msg.topic:
                    self._validate_value(
                        msg, int, [(0, 0), (6, 16)], pub_json=True)
                elif "/chargemode/pv_charging/min_soc" in msg.topic:
                    self._validate_value(msg, int, [(0, 100)], pub_json=True)
                elif "/chargemode/pv_charging/min_soc_current" in msg.topic:
                    self._validate_value(msg, int, [(6, 32)], pub_json=True)
                elif "/chargemode/pv_charging/max_soc" in msg.topic:
                    self._validate_value(msg, int, [(0, 101)], pub_json=True)
                elif "/chargemode/scheduled_charging/plans" in msg.topic:
                    self._validate_value(msg, "json")
                elif "/chargemode/scheduled_charging" in msg.topic:
                    self._validate_value(msg, "json", pub_json=True)
                elif "/time_charging/active" in msg.topic:
                    self._validate_value(msg, bool, pub_json=True)
                elif "/time_charging/plans" in msg.topic:
                    self._validate_value(msg, "json")
                else:
                    self._validate_value(msg, "json")
            elif "ev_template" in msg.topic:
                self._validate_value(msg, "json")
            else:
                self.__unknown_topic(msg)
        except Exception:
            log.exception(f"Fehler im setdata-Modul: Topic {msg.topic}, Value: {msg.payload}")

    def process_chargepoint_topic(self, msg: mqtt.MQTTMessage):
        """ Handler für die Ladepunkt-Topics

         Parameters
        ----------

        msg:
            enthält Topic und Payload
        """
        try:
            if ("openWB/set/chargepoint/get/imported" in msg.topic or
                    "openWB/set/chargepoint/get/exported" in msg.topic or
                    "openWB/set/chargepoint/get/power" in msg.topic or
                    "openWB/set/chargepoint/get/daily_imported" in msg.topic or
                    "openWB/set/chargepoint/get/daily_exported" in msg.topic):
                self._validate_value(msg, float, [(0, float("inf"))])
            elif "template" in msg.topic:
                self._validate_value(msg, "json")
            elif re.search("chargepoint/[0-9]+/config$", msg.topic) is not None:
                self._validate_value(msg, "json")
            elif subdata.SubData.cp_data.get(f"cp{get_index(msg.topic)}"):
                if ("/set/charging_ev" in msg.topic or
                        "/set/charging_ev_prev" in msg.topic):
                    self._validate_value(msg, int, [(-1, float("inf"))])
                elif "/set/current" in msg.topic:
                    self._validate_value(msg, float, [(6, 32), (0, 0)])
                elif ("/set/energy_to_charge" in msg.topic or
                        "/set/required_power" in msg.topic):
                    self._validate_value(msg, float, [(0, float("inf"))])
                elif "/set/phases_to_use" in msg.topic:
                    self._validate_value(msg, int, [(0, 3)])
                elif ("/set/manual_lock" in msg.topic or
                        "/set/perform_control_pilot_interruption" in msg.topic or
                        "/set/perform_phase_switch" in msg.topic or
                        "/set/plug_state_prev" in msg.topic):
                    self._validate_value(msg, bool)
                elif "/set/autolock_state" in msg.topic:
                    self._validate_value(msg, int, [(0, 4)])
                elif ("/set/rfid" in msg.topic or
                        "/set/plug_time" in msg.topic):
                    self._validate_value(msg, str)
                elif "/set/log" in msg.topic:
                    self._validate_value(msg, "json")
                elif "/set/change_ev_permitted" in msg.topic:
                    self._validate_value(msg, "json")
                elif "/config/ev" in msg.topic:
                    self._validate_value(
                        msg, int, [(0, float("inf"))], pub_json=True)
                elif ("/get/voltages" in msg.topic):
                    self._validate_value(
                        msg, float, [(0, 500)], collection=list)
                elif ("/get/currents" in msg.topic):
                    self._validate_value(
                        msg, float, collection=list)
                elif ("/get/power_factors" in msg.topic):
                    self._validate_value(
                        msg, float, [(-1, 1)], collection=list)
                elif ("/get/daily_imported" in msg.topic or
                        "/get/daily_exported" in msg.topic or
                        "/get/power" in msg.topic or
                        "/get/imported" in msg.topic or
                        "/get/exported" in msg.topic):
                    self._validate_value(msg, float, [(0, float("inf"))])
                elif "/get/phases_in_use" in msg.topic:
                    self._validate_value(msg, int, [(0, 3)])
                elif ("/get/charge_state" in msg.topic or
                        "/get/plug_state" in msg.topic):
                    self._validate_value(msg, bool)
                elif "/get/fault_state" in msg.topic:
                    self._validate_value(msg, int, [(0, 2)])
                elif ("/get/fault_str" in msg.topic or
                        "/get/state_str" in msg.topic or
                        "/get/heartbeat" in msg.topic):
                    self._validate_value(msg, str)
                elif ("/get/rfid" in msg.topic or
                        "/get/rfid_timestamp" in msg.topic):
                    self._validate_value(msg, str)
                else:
                    self.__unknown_topic(msg)
            else:
                log.warning(f"Kein Ladepunkt {get_index(msg.topic)} mit gültiger Konfiguration gefunden.")
        except Exception:
            log.exception(f"Fehler im setdata-Modul: Topic {msg.topic}, Value: {msg.payload}")

    def process_pv_topic(self, msg: mqtt.MQTTMessage):
        """ Handler für die PV-Topics

         Parameters
        ----------

        msg:
            enthält Topic und Payload
        """
        try:
            if "openWB/set/pv/config/configured" in msg.topic:
                self._validate_value(msg, bool)
            elif ("openWB/set/pv/get/daily_exported" in msg.topic or
                    "openWB/set/pv/get/monthly_exported" in msg.topic or
                    "openWB/set/pv/get/yearly_exported" in msg.topic):
                self._validate_value(msg, float, [(0, float("inf"))])
            elif "openWB/set/pv/get/exported" in msg.topic:
                self._validate_value(msg, float, [(0, float("inf"))])
            elif "openWB/set/pv/get/power" in msg.topic:
                self._validate_value(msg, float)
            elif "/config/max_ac_out" in msg.topic:
                self._validate_value(msg, int, [(0, float("inf"))])
            elif subdata.SubData.pv_data.get(f"pv{get_index(msg.topic)}"):
                if "/get/fault_state" in msg.topic:
                    self._validate_value(msg, int, [(0, 2)])
                elif "/get/fault_str" in msg.topic:
                    self._validate_value(msg, str)
                elif ("/get/daily_exported" in msg.topic or
                        "/get/monthly_exported" in msg.topic or
                        "/get/yearly_exported" in msg.topic or
                        "/get/energy" in msg.topic):
                    self._validate_value(msg, float, [(0, float("inf"))])
                elif "/get/exported" in msg.topic:
                    self._validate_value(msg, float, [(0, float("inf"))])
                elif "/get/power" in msg.topic:
                    self._validate_value(msg, float)
                elif "/get/currents" in msg.topic:
                    self._validate_value(
                        msg, float, collection=list)
                else:
                    self.__unknown_topic(msg)
            else:
                log.warning(f"Kein Wechselrichter {get_index(msg.topic)} mit gültiger Konfiguration gefunden.")
        except Exception:
            log.exception(f"Fehler im setdata-Modul: Topic {msg.topic}, Value: {msg.payload}")

    def process_bat_topic(self, msg: mqtt.MQTTMessage):
        """ Handler für die Hausspeicher-Topics

         Parameters
        ----------

        msg:
            enthält Topic und Payload
        """
        try:
            if ("openWB/set/bat/config/configured" in msg.topic or
                    "openWB/set/bat/set/switch_on_soc_reached" in msg.topic):
                self._validate_value(msg, bool)
            elif "openWB/set/bat/set/charging_power_left" in msg.topic:
                self._validate_value(msg, float)
            elif "openWB/set/bat/get/soc" in msg.topic:
                self._validate_value(msg, float, [(0, 100)])
            elif "openWB/set/bat/get/power" in msg.topic:
                self._validate_value(msg, float)
            elif ("openWB/set/bat/get/imported" in msg.topic or
                    "openWB/set/bat/get/exported" in msg.topic or
                    "openWB/set/bat/get/daily_exported" in msg.topic or
                    "openWB/set/bat/get/daily_imported" in msg.topic):
                self._validate_value(msg, float, [(0, float("inf"))])
            elif "/config" in msg.topic:
                self._validate_value(msg, "json")
            elif "/get/power" in msg.topic:
                self._validate_value(msg, float)
            elif subdata.SubData.bat_data.get(f"bat{get_index(msg.topic)}"):
                if ("/get/imported" in msg.topic or
                        "/get/exported" in msg.topic or
                        "/get/daily_exported" in msg.topic or
                        "/get/daily_imported" in msg.topic):
                    self._validate_value(msg, float, [(0, float("inf"))])
                elif "/get/soc" in msg.topic:
                    self._validate_value(msg, float, [(0, 100)])
                elif "/get/fault_state" in msg.topic:
                    self._validate_value(msg, int, [(0, 2)])
                elif "/get/fault_str" in msg.topic:
                    self._validate_value(msg, str)
                else:
                    self.__unknown_topic(msg)
            else:
                log.warning(f"Kein Speicher {get_index(msg.topic)} mit gültiger Konfiguration gefunden.")
        except Exception:
            log.exception(f"Fehler im setdata-Modul: Topic {msg.topic}, Value: {msg.payload}")

    def process_general_topic(self, msg: mqtt.MQTTMessage):
        """ Handler für die Allgemeinen-Topics

         Parameters
        ----------

        msg:
            enthält Topic und Payload
        """
        try:
            if "openWB/set/general/extern_display_mode" in msg.topic:
                self._validate_value(msg, str)
            elif "openWB/set/general/extern" in msg.topic:
                self._validate_value(msg, bool)
            elif "openWB/set/general/control_interval" in msg.topic:
                self._validate_value(msg, int, [(10, 10), (20, 20), (60, 60)])
            elif "openWB/set/general/external_buttons_hw" in msg.topic:
                self._validate_value(msg, bool)
            elif "openWB/set/general/chargemode_config/unbalanced_load_limit" in msg.topic:
                self._validate_value(msg, int, [(10, 32)])
            elif "openWB/set/general/chargemode_config/unbalanced_load" in msg.topic:
                self._validate_value(msg, bool)
            elif ("openWB/set/general/chargemode_config/pv_charging/feed_in_yield" in msg.topic or
                    "openWB/set/general/chargemode_config/pv_charging/switch_on_threshold" in msg.topic or
                    "openWB/set/general/chargemode_config/pv_charging/switch_on_delay" in msg.topic or
                    "openWB/set/general/chargemode_config/pv_charging/switch_off_threshold" in msg.topic or
                    "openWB/set/general/chargemode_config/pv_charging/switch_off_delay" in msg.topic):
                self._validate_value(msg, int, [(0, float("inf"))])
            elif "openWB/set/general/chargemode_config/pv_charging/phase_switch_delay" in msg.topic:
                self._validate_value(msg, int, [(1, 15)])
            elif "openWB/set/general/chargemode_config/pv_charging/control_range" in msg.topic:
                self._validate_value(msg, int, collection=list)
            elif (("openWB/set/general/chargemode_config/pv_charging/phases_to_use" in msg.topic or
                    "openWB/set/general/chargemode_config/scheduled_charging/phases_to_use" in msg.topic)):
                self._validate_value(msg, int, [(0, 0), (1, 1), (3, 3)])
            elif "openWB/set/general/chargemode_config/pv_charging/bat_prio" in msg.topic:
                self._validate_value(msg, bool)
            elif ("openWB/set/general/chargemode_config/pv_charging/switch_on_soc" in msg.topic or
                    "openWB/set/general/chargemode_config/pv_charging/switch_off_soc" in msg.topic or
                    "openWB/set/general/chargemode_config/pv_charging/rundown_soc" in msg.topic):
                self._validate_value(msg, int, [(0, 100)])
            elif ("openWB/set/general/chargemode_config/pv_charging/rundown_power" in msg.topic or
                    "openWB/set/general/chargemode_config/pv_charging/charging_power_reserve" in msg.topic):
                self._validate_value(msg, float, [(0, float("inf"))])
            elif "openWB/set/general/chargemode_config/" in msg.topic and "/phases_to_use" in msg.topic:
                self._validate_value(msg, int, [(1, 1), (3, 3)])
            elif ("openWB/set/general/grid_protection_configured" in msg.topic or
                    "openWB/set/general/grid_protection_active" in msg.topic or
                    "openWB/set/general/mqtt_bridge" in msg.topic):
                self._validate_value(msg, bool)
            elif "openWB/set/general/grid_protection_timestamp" in msg.topic:
                self._validate_value(msg, str)
            elif "openWB/set/general/grid_protection_random_stop" in msg.topic:
                self._validate_value(msg, int, [(0, 90)])
            elif "openWB/set/general/notifications/selected" in msg.topic:
                self._validate_value(msg, str)
            elif "openWB/set/general/notifications/configuration" in msg.topic:
                self._validate_value(msg, "json")
            elif ("openWB/set/general/notifications/start_charging" in msg.topic or
                    "openWB/set/general/notifications/stop_charging" in msg.topic or
                    "openWB/set/general/notifications/plug" in msg.topic or
                    "openWB/set/general/notifications/smart_home" in msg.topic):
                self._validate_value(msg, bool)
            elif "openWB/set/general/price_kwh" in msg.topic:
                self._validate_value(msg, float, [(0, 99.99)])
            elif "openWB/set/general/range_unit" in msg.topic:
                self._validate_value(msg, str)
            elif ("openWB/set/general/ripple_control_receiver/configured" in msg.topic or
                    "openWB/set/general/ripple_control_receiver/r1_active" in msg.topic or
                    "openWB/set/general/ripple_control_receiver/r2_active" in msg.topic):
                self._validate_value(msg, bool)
            else:
                self.__unknown_topic(msg)
        except Exception:
            log.exception(f"Fehler im setdata-Modul: Topic {msg.topic}, Value: {msg.payload}")

    def process_optional_topic(self, msg: mqtt.MQTTMessage):
        """ Handler für die Optionalen-Topics

         Parameters
        ----------

        msg:
            enthält Topic und Payload
        """
        try:
            if "openWB/set/optional/load_sharing/active" in msg.topic:
                self._validate_value(msg, bool)
            elif "openWB/set/optional/load_sharing/max_current" in msg.topic:
                self._validate_value(msg, int, [(16, 32)])
            elif "openWB/set/optional/et/active" in msg.topic:
                self._validate_value(msg, bool)
            elif "openWB/set/optional/et/get/price_list" in msg.topic:
                self._validate_value(msg, "json")
            elif "openWB/set/optional/et/get/price" in msg.topic:
                self._validate_value(msg, float)
            elif "openWB/set/optional/et/get/source" in msg.topic:
                self._validate_value(msg, str)
            elif "openWB/set/optional/et/config/max_price" in msg.topic:
                self._validate_value(msg, float)
            elif "openWB/set/optional/et/config/provider" in msg.topic:
                self._validate_value(msg, "json")
            elif "openWB/set/optional/rfid/active" in msg.topic:
                self._validate_value(msg, bool)
            elif "openWB/set/optional/int_display/active" in msg.topic:
                self._validate_value(msg, bool)
            elif "openWB/set/optional/int_display/on_if_plugged_in" in msg.topic:
                self._validate_value(msg, bool)
            elif "openWB/set/optional/int_display/pin_active" in msg.topic:
                self._validate_value(msg, bool)
            elif "openWB/set/optional/int_display/pin_code" in msg.topic:
                self._validate_value(msg, str)
            elif "openWB/set/optional/int_display/standby" in msg.topic:
                self._validate_value(msg, int, [(0, 300)])
            elif "openWB/set/optional/int_display/theme" in msg.topic:
                self._validate_value(msg, str)
            elif "openWB/set/optional/led/active" in msg.topic:
                self._validate_value(msg, bool)
            else:
                self.__unknown_topic(msg)
        except Exception:
            log.exception(f"Fehler im setdata-Modul: Topic {msg.topic}, Value: {msg.payload}")

    def process_counter_topic(self, msg: mqtt.MQTTMessage):
        """ Handler für die Zähler-Topics

         Parameters
        ----------

        msg:
            enthält Topic und Payload
        """
        try:
            if "openWB/set/counter/set/loadmanagement_active" in msg.topic:
                self._validate_value(msg, bool)
            elif "openWB/set/counter/set/invalid_home_consumption" in msg.topic:
                self._validate_value(msg, int, [(0, 3)])
            elif ("openWB/set/counter/set/home_consumption" in msg.topic or
                    "openWB/set/counter/set/daily_yield_home_consumption" in msg.topic):
                self._validate_value(msg, float, [(0, float("inf"))])
            elif "openWB/set/counter/get/hierarchy" in msg.topic:
                self._validate_value(msg, None)
            elif "/set/consumption_left" in msg.topic:
                self._validate_value(msg, float)
            elif "/config/selected" in msg.topic:
                self._validate_value(msg, str)
            elif "/module" in msg.topic:
                self._validate_value(msg, "json")
            elif "/config/max_currents" in msg.topic:
                self._validate_value(msg, int, [(7, 1500)], collection=list)
            elif "/config/max_total_power" in msg.topic:
                self._validate_value(msg, int, [(0,  float("inf"))])
            elif subdata.SubData.counter_data.get(f"counter{get_index(msg.topic)}"):
                if ("/get/powers" in msg.topic or
                        "/get/currents" in msg.topic):
                    self._validate_value(
                        msg, float, collection=list)
                elif ("/get/voltages" in msg.topic):
                    self._validate_value(
                        msg, float, [(0, 500)], collection=list)
                elif ("/get/power_factors" in msg.topic):
                    self._validate_value(
                        msg, float, [(-1, 1)], collection=list)
                elif ("/get/power_average" in msg.topic
                        or "/get/unbalanced_load" in msg.topic
                        or "/get/frequency" in msg.topic
                        or "/get/daily_exported" in msg.topic
                        or "/get/daily_imported" in msg.topic
                        or "/get/imported" in msg.topic
                        or "/get/exported" in msg.topic):
                    self._validate_value(
                        msg, float, [(0, float("inf"))])
                elif "/get/fault_state" in msg.topic:
                    self._validate_value(msg, int, [(0, 2)])
                elif ("/get/fault_str" in msg.topic or
                      "/set/state_str" in msg.topic):
                    self._validate_value(msg, str)
                elif "/get/power" in msg.topic:
                    self._validate_value(
                        msg, float, [(float("-inf"), float("inf"))])
                elif ("/set/reserved_surplus" in msg.topic or
                      "set/released_surplus" in msg.topic):
                    self._validate_value(msg, float)
                else:
                    self.__unknown_topic(msg)
            else:
                log.warning(f"Kein Zähler {get_index(msg.topic)} mit gültiger Konfiguration gefunden.")
        except Exception:
            log.exception(f"Fehler im setdata-Modul: Topic {msg.topic}, Value: {msg.payload}")

    def process_log_topic(self, msg: mqtt.MQTTMessage):
        """Handler für die Log-Topics

         Parameters
        ----------

        msg:
            enthält Topic und Payload
        """
        try:
            if ("openWB/set/log/" and "data" in msg.topic or
                    "openWB/set/log/daily" in msg.topic or
                    "openWB/set/log/monthly" in msg.topic):
                self._validate_value(msg, "json", retain=False)
            else:
                self.__unknown_topic(msg)
        except Exception:
            log.exception(f"Fehler im setdata-Modul: Topic {msg.topic}, Value: {msg.payload}")

    def process_graph_topic(self, msg: mqtt.MQTTMessage):
        """Handler für die Graph-Topics

         Parameters
        ----------
        msg:
            enthält Topic und Payload
        """
        try:
            if ("alllivevaluesJson" in msg.topic or
                    "openWB/set/graph/lastlivevaluesJson" in msg.topic):
                self._validate_value(msg, "json")
            elif "config" in msg.topic:
                if "duration" in msg.topic:
                    self._validate_value(msg, int, [(10, 120)])
            else:
                self.__unknown_topic(msg)
        except Exception:
            log.exception(f"Fehler im setdata-Modul: Topic {msg.topic}, Value: {msg.payload}")

    def process_system_topic(self, msg: mqtt.MQTTMessage):
        """Handler für die System-Topics

         Parameters
        ----------
        msg:
            enthält Topic und Payload
        """
        try:
            if "openWB/set/system/lastlivevaluesJson" in msg.topic:
                self._validate_value(msg, "json")
            elif ("openWB/set/system/perform_update" in msg.topic or
                    "openWB/set/system/wizard_done" in msg.topic or
                    "openWB/set/system/update_in_progress" in msg.topic or
                    "openWB/set/system/dataprotection_acknowledged" in msg.topic):
                self._validate_value(msg, bool)
            elif "openWB/set/system/version" in msg.topic:
                self._validate_value(msg, str)
            elif "openWB/set/system/datastore_version" in msg.topic:
                self._validate_value(msg, int, [(0, UpdateConfig.DATASTORE_VERSION)])
            elif "openWB/set/system/GetRemoteSupport" in msg.topic:
                # Server-Topic enthält kein json-Payload.
                payload = msg.payload.decode("utf-8")
                if isinstance(payload, str):
                    Pub().pub(msg.topic.replace('set/', '', 1), payload)
                    Pub().pub(msg.topic, "")
                else:
                    log.error(f"Payload ungültig: Topic {msg.topic}, Payload {payload} sollte ein String sein.")
                    Pub().pub(msg.topic, "")
            elif "openWB/set/system/debug_level" in msg.topic:
                self._validate_value(msg, int, [(10, 10), (20, 20), (30, 30)])
            elif ("openWB/set/system/ip_address" in msg.topic or
                    "openWB/set/system/release_train" in msg.topic):
                self._validate_value(msg, str)
            elif "openWB/set/system/mqtt/bridge/" in msg.topic:
                self._validate_value(msg, "json")
            elif "configurable" in msg.topic:
                self._validate_value(msg, None)
            elif "device" in msg.topic:
                if "component" in msg.topic:
                    if "/simulation" in msg.topic:
                        self._validate_value(msg, "json")
                    elif "/config" in msg.topic:
                        self._validate_value(msg, "json")
                    else:
                        self.__unknown_topic(msg)
                elif "/config" in msg.topic:
                    self._validate_value(msg, "json")
                elif "/get/fault_state" in msg.topic:
                    self._validate_value(msg, int, [(0, 2)])
                elif "/get/fault_str" in msg.topic:
                    self._validate_value(msg, str)
                elif "module_update_completed" in msg.topic:
                    self._validate_value(msg, bool)
                else:
                    self.__unknown_topic(msg)
            else:
                # hier kommen auch noch alte Topics ohne json-Format an.
                # log.error("Unbekanntes set-Topic: "+str(msg.topic)+", "+
                # str(json.loads(str(msg.payload.decode("utf-8")))))
                Pub().pub(msg.topic, "")
        except Exception:
            log.exception(f"Fehler im setdata-Modul: Topic {msg.topic}, Value: {msg.payload}")

    def process_command_topic(self, msg: mqtt.MQTTMessage):
        """Handler für die Befehl-Topics

         Parameters
        ----------
        msg:
            enthält Topic und Payload
        """
        try:
            if "openWB/set/command/max_id" in msg.topic:
                self._validate_value(msg, int, [(-1, float("inf"))])
            elif "todo" in msg.topic:
                self._validate_value(msg, "json")
            elif "error" in msg.topic:
                self._validate_value(msg, "json")
            elif "messages" in msg.topic:
                self._validate_value(msg, "json")
            elif "command_completed" in msg.topic:
                self._validate_value(msg, bool)
            else:
                self.__unknown_topic(msg)
        except Exception:
            log.exception(f"Fehler im setdata-Modul: Topic {msg.topic}, Value: {msg.payload}")
