""" Modul, um die Daten vom Broker zu erhalten.
"""

import copy
import json
import paho.mqtt.client as mqtt
import re

from helpermodules.log import MainLogger, MqttLogger
from helpermodules.pub import Pub
from helpermodules import subdata


class SetData:

    def __init__(self, event_ev_template, event_charge_template, event_cp_config):
        self.event_ev_template = event_ev_template
        self.event_charge_template = event_charge_template
        self.event_cp_config = event_cp_config
        self.heartbeat = False

    def set_data(self):
        """ abonniert alle set-Topics.
        """
        mqtt_broker_ip = "localhost"
        self.client = mqtt.Client("openWB-mqttset-" + self.getserial())
        # ipallowed='^[0-9.]+$'
        # nameallowed='^[a-zA-Z ]+$'
        # namenumballowed='^[0-9a-zA-Z ]+$'

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(mqtt_broker_ip, 1886)
        self.client.loop_forever()

    def disconnect(self) -> None:
        self.client.disconnect()
        MainLogger().info("Verbindung von Client openWB-mqttset-" + self.getserial()+" geschlossen.")

    def getserial(self):
        """ Extract serial from cpuinfo file
        """
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line[0:6] == 'Serial':
                    return line[10:26]
            return "0000000000000000"

    def on_connect(self, client, userdata, flags, rc):
        """ connect to broker and subscribe to set topics
        """
        client.subscribe("openWB/set/#", 2)

    def on_message(self, client, userdata, msg):
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
        if str(msg.payload.decode("utf-8")) != "":
            MqttLogger().debug("Topic: "+str(msg.topic) + ", Payload: "+str(msg.payload.decode("utf-8")))
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

    def _validate_value(self, msg, data_type, ranges=[], collection=None, pub_json=False):
        """ prüft, ob der Wert vom angegebenen Typ ist.

        Parameter
        ---------
        msg:
            Broker-Nachricht
        data_type: float, int, str, "json", None
            Datentyp (None für komplexe Datenstrukturen, wie z.B. Hierarchie)
        ranges: [(int/float/None, int/float/None), ..]
            Liste mit Tuples, die die Wertebereiche enthalten (None für unendlich)
        collection = list/dict
            Angabe, ob und welche Kollektion erwartet wird
        pub_json : true/false
            gibt an, ob das Topic von openWB/set/.. an openWB/.. gepublished werden soll oder ein json-Objekt,
            dass mehrere Daten enthält.
        """
        valid = False
        try:
            value = json.loads(str(msg.payload.decode("utf-8")))
            if data_type is None or data_type == "json":
                # Wenn kein gültiges json-Objekt übergeben worden wäre, wäre bei loads eine Exception aufgetreten.
                valid = True
            elif collection is not None:
                if self._validate_collection_value(msg, data_type, ranges, collection):
                    valid = True
            elif data_type == str:
                if isinstance(value, str):
                    valid = True
                else:
                    MainLogger().error("Payload ungueltig: Topic "+str(msg.topic) +
                                       ", Payload "+str(value)+" sollte ein String sein.")
            elif data_type == int or data_type == float:
                if self._validate_min_max_value(value, msg, data_type, ranges):
                    valid = True

            if valid:
                if not pub_json:
                    Pub().pub(msg.topic.replace('set/', '', 1), value)
                    Pub().pub(msg.topic, "")
                else:
                    # aktuelles json-Objekt liegt in subdata
                    index = re.search(
                        '(?!/)([0-9]*)(?=/|$)', msg.topic).group()
                    if "charge_template" in msg.topic:
                        event = self.event_charge_template
                        if "ct"+str(index) in subdata.SubData.ev_charge_template_data:
                            template = copy.deepcopy(
                                subdata.SubData.ev_charge_template_data["ct"+str(index)].data)
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
                            template = copy.deepcopy(
                                subdata.SubData.cp_data["cp"+str(index)].data["config"])
                        else:
                            template = {}
                    else:
                        raise ValueError(
                            "Zu "+msg.topic+" konnte kein passendes json-Objekt gefunden werden.")
                    # Wert, der aktualisiert werden soll, erstellen/finden und updaten
                    if event == self.event_cp_config:
                        key_list = msg.topic.split("/")[5:]
                    else:
                        key_list = msg.topic.split("/")[6:]
                    self._change_key(template, key_list, value)
                    # publish
                    index_pos = re.search(
                        '(?!/)([0-9]*)(?=/|$)', msg.topic).end()
                    if event == self.event_cp_config:
                        topic = msg.topic[:index_pos]+"/config"
                    else:
                        topic = msg.topic[:index_pos]
                    topic = topic.replace('set/', '', 1)
                    Pub().pub(topic, template)
                    Pub().pub(msg.topic, "")
                    event.clear()
            else:
                Pub().pub(msg.topic, "")
        except Exception:
            MainLogger().exception("Fehler im setdata-Modul")
            Pub().pub(msg.topic, "")

    def _change_key(self, next_level, key_list, value):
        """ rekursive Funktion, die den Eintrag im entsprechenden Dictionary aktualisiert oder anlegt.

        Parameter
        ---------
        next_level: dict
            Beim ersten Aufruf: Dictionary, das aktualisiert werden soll.
            Danach: Dictionary aus den verschachtelten Dictionarys, das gerade betrachtet werden soll.
        key_list: list
            Liste der Keys aus den verschachtelten Dictionarys, unter denen der Eintrag zu finden ist.
        value:
            Wert, der geschrieben werden soll.
        """
        try:
            if len(key_list) == 1:
                next_level[key_list[0]] = value
            else:
                if key_list[0] not in next_level:
                    next_level[key_list[0]] = {}
                next_key = key_list[0]
                key_list.pop(0)
                self._change_key(next_level[next_key], key_list, value)
        except Exception:
            MainLogger().exception("Fehler im setdata-Modul")

    def _validate_collection_value(self, msg, data_type, ranges=None, collection=None):
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
            value = json.loads(str(msg.payload.decode("utf-8")))
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
                MainLogger().error("Payload ungueltig: Topic "+str(msg.topic)+", Payload " +
                                   str(value)+" sollte eine Kollektion vom Typ "+str(collection)+" sein.")
            return valid
        except Exception:
            MainLogger().exception("Fehler im setdata-Modul")

    def _validate_min_max_value(self, value, msg, data_type, ranges=None):
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
            # wird, falls erfoderlich.
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
                        MainLogger().error("Payload ungueltig: Topic "+str(msg.topic)+", Payload " +
                                           str(value)+" liegt in keinem der angegebenen Wertebereiche.")
                        valid = False
            elif value is None:
                for range in ranges:
                    if range[0] is None and range[1] is None:
                        break
                else:
                    MainLogger().error("Payload ungueltig: Topic "+str(msg.topic) +
                                       ", Payload "+str(value)+" darf nicht 'None' sein.")
                    valid = False
            else:
                if data_type == int:
                    MainLogger().error("Payload ungueltig: Topic "+str(msg.topic) +
                                       ", Payload "+str(value)+" sollte ein Int sein.")
                elif data_type == float:
                    MainLogger().error("Payload ungueltig: Topic "+str(msg.topic) +
                                       ", Payload "+str(value)+" sollte ein Float sein.")
                valid = False
            return valid
        except Exception:
            MainLogger().exception("Fehler im setdata-Modul")

    def __unknown_topic(self, msg) -> None:
        try:
            if msg.payload:
                MainLogger().error("Unbekanntes set-Topic: "+str(msg.topic) +
                                   ", " + str(json.loads(str(msg.payload.decode("utf-8")))))
                Pub().pub(msg.topic, "")
            else:
                MainLogger().error("Unbekanntes set-Topic: " +
                                   str(msg.topic)+" mit leerem Payload")
                Pub().pub(msg.topic, "")
        except Exception:
            MainLogger().exception("Fehler im setdata-Modul")

    def process_vehicle_topic(self, msg):
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
            elif "/soc_module/config" in msg.topic:
                self._validate_value(msg, "json")
            elif "/soc/get/fault_state" in msg.topic:
                self._validate_value(msg, int, [(0, 2)])
            elif "/soc/get/fault_str" in msg.topic:
                self._validate_value(msg, str)
            elif "/tag_id" in msg.topic:
                self._validate_value(msg, str, collection=list)
            elif "/set/ev_template" in msg.topic:
                self._validate_value(msg, "json")
            elif ("/charge_template" in msg.topic or
                    "/ev_template" in msg.topic):
                self._validate_value(msg, int, [(0, float("inf"))])
            elif "/get/soc_timestamp" in msg.topic:
                self._validate_value(msg, int, [(0, float("inf"))])
            elif "/get/soc" in msg.topic:
                self._validate_value(msg, float, [(0, 100)])
            elif "/get/timestamp_last_request" in msg.topic:
                self._validate_value(msg, str)
            elif "/control_parameter/required_current" in msg.topic:
                self._validate_value(msg, float, [(6, 32), (0, 0)])
            elif "/control_parameter/phases" in msg.topic:
                self._validate_value(msg, int, [(0, 3)])
            elif ("/control_parameter/submode" in msg.topic or
                    "/control_parameter/chargemode" in msg.topic):
                self._validate_value(msg, str)
            elif "/control_parameter/prio" in msg.topic:
                self._validate_value(msg, int, [(0, 1)])
            elif ("/control_parameter/timestamp_switch_on_off" in msg.topic or
                    "/control_parameter/timestamp_auto_phase_switch" in msg.topic or
                    "/control_parameter/timestamp_perform_phase_switch" in msg.topic):
                self._validate_value(msg, str)
            else:
                self.__unknown_topic(msg)
        except Exception:
            MainLogger().exception("Fehler im setdata-Modul")

    def _subprocess_vehicle_chargemode_topic(self, msg):
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
                    self._validate_value(msg, int, [(0, 1)], pub_json=True)
                elif "/chargemode/selected" in msg.topic:
                    self._validate_value(msg, str, pub_json=True)
                elif "/chargemode/instant_charging/current" in msg.topic:
                    self._validate_value(msg, int, [(6, 32)], pub_json=True)
                elif "/chargemode/instant_charging/limit/selected" in msg.topic:
                    self._validate_value(msg, str, pub_json=True)
                elif "/chargemode/instant_charging/limit/soc" in msg.topic:
                    self._validate_value(msg, int, [(0, 100)], pub_json=True)
                elif "/chargemode/instant_charging/limit/amount" in msg.topic:
                    self._validate_value(msg, int, [(2, 100)], pub_json=True)
                elif "/chargemode/pv_charging/feed_in_limit" in msg.topic:
                    self._validate_value(msg, int, [(0, 1)], pub_json=True)
                elif "/chargemode/pv_charging/min_current" in msg.topic:
                    self._validate_value(
                        msg, int, [(0, 0), (6, 16)], pub_json=True)
                elif "/chargemode/pv_charging/min_soc" in msg.topic:
                    self._validate_value(msg, int, [(0, 100)], pub_json=True)
                elif "/chargemode/pv_charging/min_soc_current" in msg.topic:
                    self._validate_value(msg, int, [(6, 32)], pub_json=True)
                elif "/chargemode/pv_charging/max_soc" in msg.topic:
                    self._validate_value(msg, int, [(0, 101)], pub_json=True)
                elif "/chargemode/scheduled_charging/[0-9]+/active" in msg.topic:
                    self._validate_value(msg, int, [(0, 1)], pub_json=True)
                elif "/chargemode/scheduled_charging/plans" in msg.topic:
                    self._validate_value(msg, "json")
                elif "/chargemode/scheduled_charging" in msg.topic:
                    self._validate_value(msg, "json", pub_json=True)
                elif "/time_charging/active" in msg.topic:
                    self._validate_value(msg, int, [(0, 1)], pub_json=True)
                elif "/time_charging/plans" in msg.topic:
                    self._validate_value(msg, "json")
                else:
                    self._validate_value(msg, "json")
            elif "ev_template" in msg.topic:
                if "/name" in msg.topic:
                    self._validate_value(msg, str, pub_json=True)
                elif "/average_consump" in msg.topic:
                    self._validate_value(
                        msg, float, [(0, float("inf"))], pub_json=True)
                elif "/battery_capacity" in msg.topic:
                    self._validate_value(
                        msg, int, [(0, float("inf"))], pub_json=True)
                elif "/max_phases" in msg.topic:
                    self._validate_value(msg, int, [(1, 3)], pub_json=True)
                elif "/min_current" in msg.topic:
                    self._validate_value(msg, int, [(6, 32)], pub_json=True)
                elif ("/max_current_one_phase" in msg.topic or
                        "/max_current_multi_phases" in msg.topic):
                    self._validate_value(
                        msg, int, [(0, 0), (6, 32)], pub_json=True)
                elif ("/control_pilot_interruption" in msg.topic or
                        "/prevent_switch_stop" in msg.topic):
                    self._validate_value(msg, int, [(0, 1)], pub_json=True)
                elif "/control_pilot_interruption_duration" in msg.topic:
                    self._validate_value(msg, int, [(4, 15)], pub_json=True)
                elif "/nominal_difference" in msg.topic:
                    self._validate_value(msg, float, [(0, 4)], pub_json=True)
                elif "/phase_switch_pause" in msg.topic:
                    self._validate_value(msg, int, [(2, 150)], pub_json=True)
                else:
                    self._validate_value(msg, "json")
            else:
                self.__unknown_topic(msg)
        except Exception:
            MainLogger().exception("Fehler im setdata-Modul")

    def process_chargepoint_topic(self, msg):
        """ Handler für die Ladepunkt-Topics

         Parameters
        ----------

        msg:
            enthält Topic und Payload
        """
        try:
            if ("openWB/set/chargepoint/get/counter_all" in msg.topic or
                    "openWB/set/chargepoint/get/power_all" in msg.topic or
                    "openWB/set/chargepoint/get/daily_yield" in msg.topic):
                self._validate_value(msg, float, [(0, float("inf"))])
            elif "template" in msg.topic:
                self._validate_value(msg, "json")
            elif ("/set/charging_ev" in msg.topic or
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
                    "/set/perform_phase_switch" in msg.topic):
                self._validate_value(msg, int, [(0, 1)])
            elif "/set/autolock_state" in msg.topic:
                self._validate_value(msg, int, [(0, 4)])
            elif "/set/rfid" in msg.topic:
                self._validate_value(msg, str)
            elif ("/set/log/time_charged" in msg.topic or
                    "/set/log/chargemode_log_entry" in msg.topic or
                    "/set/plug_time" in msg.topic):
                self._validate_value(msg, str)
            elif "/set/change_ev_permitted" in msg.topic:
                self._validate_value(msg, "json")
            elif ("/set/log/range_charged" in msg.topic or
                    "/set/log/counter" in msg.topic or
                    "/set/log/charged_since_mode_switch" in msg.topic or
                    "/set/log/charged_since_plugged_counter" in msg.topic or
                    "/set/log/counter_at_mode_switch" in msg.topic or
                    "/set/log/counter_at_plugtime" in msg.topic):
                self._validate_value(msg, float, [(0, float("inf"))])
            elif "/set/log/timestamp_start_charging" in msg.topic:
                self._validate_value(msg, str)
            elif "/config/ev" in msg.topic:
                self._validate_value(
                    msg, int, [(0, float("inf"))], pub_json=True)
            elif "/config" in msg.topic:
                self._validate_value(msg, "json")
            elif ("/get/voltage" in msg.topic or
                    "/get/current" in msg.topic or
                    "/get/power_factor" in msg.topic):
                self._validate_value(
                    msg, float, [(0, float("inf"))], collection=list)
            elif ("/get/daily_yield" in msg.topic or
                    "/get/power_all" in msg.topic or
                    "/get/counter" in msg.topic or
                    "/get/exported" in msg.topic):
                self._validate_value(msg, float, [(0, float("inf"))])
            elif "/get/phases_in_use" in msg.topic:
                self._validate_value(msg, int, [(0, 3)])
            elif ("/get/charge_state" in msg.topic or
                    "/get/plug_state" in msg.topic):
                self._validate_value(msg, int, [(0, 1)])
            elif "/get/fault_state" in msg.topic:
                self._validate_value(msg, int, [(0, 2)])
            elif ("/get/fault_str" in msg.topic or
                    "/get/state_str" in msg.topic or
                    "/get/heartbeat" in msg.topic):
                self._validate_value(msg, str)
            elif "/get/read_tag" in msg.topic:
                self._validate_value(msg, "json")
            elif "/get/rfid" in msg.topic:
                # isss Anpassung muss noch in die nightly
                Pub().pub(msg.topic, "")
            else:
                self.__unknown_topic(msg)
        except Exception:
            MainLogger().exception("Fehler im setdata-Modul")

    def process_pv_topic(self, msg):
        """ Handler für die PV-Topics

         Parameters
        ----------

        msg:
            enthält Topic und Payload
        """
        try:
            if "openWB/set/pv/config/configured" in msg.topic:
                self._validate_value(msg, int, [(0, 1)])
            elif ("openWB/set/pv/get/daily_yield" in msg.topic or
                    "openWB/set/pv/get/monthly_yield" in msg.topic or
                    "openWB/set/pv/get/yearly_yield" in msg.topic):
                self._validate_value(msg, float, [(0, float("inf"))])
            elif "openWB/set/pv/get/counter" in msg.topic:
                self._validate_value(msg, float, [(0, float("inf"))])
            elif "openWB/set/pv/get/power" in msg.topic:
                self._validate_value(msg, float, [(float("-inf"), 0)])
            elif ("openWB/set/pv/set/overhang_power_left" in msg.topic or
                    "openWB/set/pv/set/reserved_evu_overhang" in msg.topic or
                    "openWB/set/pv/set/released_evu_overhang" in msg.topic):
                self._validate_value(msg, float)
            elif "openWB/set/pv/set/available_power" in msg.topic:
                self._validate_value(msg, float)
            elif "/config" in msg.topic:
                self._validate_value(msg, "json")
            elif "/get/fault_state" in msg.topic:
                self._validate_value(msg, int, [(0, 2)])
            elif ("/get/fault_str" in msg.topic or
                    "/get/simulation/timestamp_present" in msg.topic):
                self._validate_value(msg, str)
            elif ("/get/daily_yield" in msg.topic or
                    "/get/monthly_yield" in msg.topic or
                    "/get/yearly_yield" in msg.topic or
                    "/get/energy" in msg.topic):
                self._validate_value(msg, float, [(0, float("inf"))])
            elif "/get/counter" in msg.topic:
                self._validate_value(msg, float, [(0, float("inf"))])
            elif ("/get/counter_offset" in msg.topic or
                    "/get/counter_start" in msg.topic or
                    "/get/simulation/power_present" in msg.topic or
                    "/get/simulation/present_imported" in msg.topic or
                    "/get/simulation/present_exported" in msg.topic):
                self._validate_value(msg, float)
            elif "/get/power" in msg.topic:
                self._validate_value(msg, float, [(float("-inf"), 0)])
            elif "/get/currents" in msg.topic:
                self._validate_value(
                    msg, float, [(float("-inf"), 0)], collection=list)
            else:
                self.__unknown_topic(msg)
        except Exception:
            MainLogger().exception("Fehler im setdata-Modul")

    def process_bat_topic(self, msg):
        """ Handler für die Hausspeicher-Topics

         Parameters
        ----------

        msg:
            enthält Topic und Payload
        """
        try:
            if ("openWB/set/bat/config/configured" in msg.topic or
                    "openWB/set/bat/set/switch_on_soc_reached" in msg.topic or
                    "openWB/set/bat/set/hybrid_system_detected" in msg.topic):
                self._validate_value(msg, int, [(0, 1)])
            elif "openWB/set/bat/set/charging_power_left" in msg.topic:
                self._validate_value(msg, float)
            elif "openWB/set/bat/get/soc" in msg.topic:
                self._validate_value(msg, float, [(0, 100)])
            elif "openWB/set/bat/get/power" in msg.topic:
                self._validate_value(msg, float)
            elif ("openWB/set/bat/get/imported" in msg.topic or
                    "openWB/set/bat/get/exported" in msg.topic or
                    "openWB/set/bat/get/daily_yield_export" in msg.topic or
                    "openWB/set/bat/get/daily_yield_import" in msg.topic):
                self._validate_value(msg, float, [(0, float("inf"))])
            elif "/config" in msg.topic:
                self._validate_value(msg, "json")
            elif ("/get/power" in msg.topic or
                    "/get/simulation/power_present" in msg.topic or
                    "/get/simulation/present_imported" in msg.topic or
                    "/get/simulation/present_exported" in msg.topic):
                self._validate_value(msg, float)
            elif ("/get/imported" in msg.topic or
                    "/get/exported" in msg.topic or
                    "/get/daily_yield_export" in msg.topic or
                    "/get/daily_yield_import" in msg.topic):
                self._validate_value(msg, float, [(0, float("inf"))])
            elif "/get/soc" in msg.topic:
                self._validate_value(msg, float, [(0, 100)])
            elif "/get/fault_state" in msg.topic:
                self._validate_value(msg, int, [(0, 2)])
            elif ("/get/fault_str" in msg.topic or
                    "/get/simulation/timestamp_present" in msg.topic):
                self._validate_value(msg, str)
            else:
                self.__unknown_topic(msg)
        except Exception:
            MainLogger().exception("Fehler im setdata-Modul")

    def process_general_topic(self, msg):
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
                self._validate_value(msg, int, [(0, 1)])
            elif "openWB/set/general/control_interval" in msg.topic:
                self._validate_value(msg, int, [(10, 10), (20, 20), (60, 60)])
            elif "openWB/set/general/external_buttons_hw" in msg.topic:
                self._validate_value(msg, int, [(0, 1)])
            elif "openWB/set/general/chargemode_config/individual_mode" in msg.topic:
                self._validate_value(msg, int, [(0, 1)])
            elif "openWB/set/general/chargemode_config/unbalanced_load_limit" in msg.topic:
                self._validate_value(msg, int, [(10, 32)])
            elif "openWB/set/general/chargemode_config/unbalanced_load" in msg.topic:
                self._validate_value(msg, int, [(0, 1)])
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
                self._validate_value(msg, int, [(0, 1)])
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
                self._validate_value(msg, int, [(0, 1)])
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
                self._validate_value(msg, int, [(0, 1)])
            elif "openWB/set/general/price_kwh" in msg.topic:
                self._validate_value(msg, float, [(0, 99.99)])
            elif "openWB/set/general/range_unit" in msg.topic:
                self._validate_value(msg, str)
            elif ("openWB/set/general/ripple_control_receiver/configured" in msg.topic or
                    "openWB/set/general/ripple_control_receiver/r1_active" in msg.topic or
                    "openWB/set/general/ripple_control_receiver/r2_active" in msg.topic):
                self._validate_value(msg, int, [(0, 1)])
            else:
                self.__unknown_topic(msg)
        except Exception:
            MainLogger().exception("Fehler im setdata-Modul")

    def process_optional_topic(self, msg):
        """ Handler für die Optionalen-Topics

         Parameters
        ----------

        msg:
            enthält Topic und Payload
        """
        try:
            if "openWB/set/optional/load_sharing/active" in msg.topic:
                self._validate_value(msg, int, [(0, 1)])
            elif "openWB/set/optional/load_sharing/max_current" in msg.topic:
                self._validate_value(msg, int, [(16, 32)])
            elif "openWB/set/optional/et/active" in msg.topic:
                self._validate_value(msg, int, [(0, 1)])
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
                self._validate_value(msg, int, [(0, 1)])
            elif "openWB/set/optional/int_display/active" in msg.topic:
                self._validate_value(msg, int, [(0, 1)])
            elif "openWB/set/optional/int_display/on_if_plugged_in" in msg.topic:
                self._validate_value(msg, int, [(0, 1)])
            elif "openWB/set/optional/int_display/pin_active" in msg.topic:
                self._validate_value(msg, int, [(0, 1)])
            elif "openWB/set/optional/int_display/pin_code" in msg.topic:
                self._validate_value(msg, str)
            elif "openWB/set/optional/int_display/standby" in msg.topic:
                self._validate_value(msg, int, [(0, 300)])
            elif "openWB/set/optional/int_display/theme" in msg.topic:
                self._validate_value(msg, str)
            elif "openWB/set/optional/led/active" in msg.topic:
                self._validate_value(msg, int, [(0, 1)])
            else:
                self.__unknown_topic(msg)
        except Exception:
            MainLogger().exception("Fehler im setdata-Modul")

    def process_counter_topic(self, msg):
        """ Handler für die Zähler-Topics

         Parameters
        ----------

        msg:
            enthält Topic und Payload
        """
        try:
            if "openWB/set/counter/set/loadmanagement_active" in msg.topic:
                self._validate_value(msg, int, [(0, 1)])
            elif "openWB/set/counter/set/invalid_home_consumption" in msg.topic:
                self._validate_value(msg, int, [(0, 3)])
            elif ("openWB/set/counter/set/home_consumption" in msg.topic or
                    "openWB/set/counter/set/daily_yield_home_consumption" in msg.topic):
                self._validate_value(msg, float, [(0, float("inf"))])
            elif "openWB/set/counter/get/hierarchy" in msg.topic:
                self._validate_value(msg, None)
            elif "/set/consumption_left" in msg.topic:
                self._validate_value(msg, float)
            elif "/set/current_left" in msg.topic:
                self._validate_value(
                    msg, float, [(0, float("inf"))], collection=list)
            elif "/config/selected" in msg.topic:
                self._validate_value(msg, str)
            elif "/module" in msg.topic:
                self._validate_value(msg, "json")
            elif "/config/max_current" in msg.topic:
                self._validate_value(msg, int, [(7, 1500)], collection=list)
            elif "/config/max_total_power" in msg.topic:
                self._validate_value(msg, int, [(2000, 1000000)])
            elif "/get/power_all" in msg.topic:
                self._validate_value(
                    msg, float, [(float("-inf"), float("inf")), (None, None)])
            elif ("/get/power_phase" in msg.topic or
                    "/get/current" in msg.topic):
                self._validate_value(
                    msg, float, [(float("-inf"), float("inf")), (None, None)], collection=list)
            elif ("/get/voltage" in msg.topic or
                    "/get/power_factor" in msg.topic):
                self._validate_value(
                    msg, float, [(0, float("inf")), (None, None)], collection=list)
            elif ("/get/power_average" in msg.topic
                    or "/get/unbalanced_load" in msg.topic
                    or "/get/frequency" in msg.topic
                    or "/get/daily_yield_export" in msg.topic
                    or "/get/daily_yield_import" in msg.topic
                    or "/get/imported" in msg.topic
                    or "/get/exported" in msg.topic):
                self._validate_value(
                    msg, float, [(0, float("inf")), (None, None)])
            elif ("/get/simulation/power_present" in msg.topic or
                    "/get/simulation/present_imported" in msg.topic or
                    "/get/simulation/present_exported" in msg.topic):
                self._validate_value(msg, float)
            elif "/get/fault_state" in msg.topic:
                self._validate_value(msg, int, [(0, 2)])
            elif ("/get/fault_str" in msg.topic or
                    "/get/simulation/timestamp_present" in msg.topic):
                self._validate_value(msg, str)
            else:
                self.__unknown_topic(msg)
        except Exception:
            MainLogger().exception("Fehler im setdata-Modul")

    def process_log_topic(self, msg):
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
                self._validate_value(msg, "json")
            else:
                self.__unknown_topic(msg)
        except Exception:
            MainLogger().exception("Fehler im setdata-Modul")

    def process_graph_topic(self, msg):
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
            MainLogger().exception("Fehler im setdata-Modul")

    def process_system_topic(self, msg):
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
                    "openWB/set/system/wizzard_done" in msg.topic or
                    "openWB/set/system/update_in_progress" in msg.topic or
                    "openWB/set/system/dataprotection_acknowledged" in msg.topic):
                self._validate_value(msg, int, [(0, 1)])
            elif "openWB/set/system/remote_support" in msg.topic:
                self._validate_value(msg, str)
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
                    if "/config" in msg.topic:
                        self._validate_value(msg, "json")
                    else:
                        self.__unknown_topic(msg)
                elif "/config" in msg.topic:
                    self._validate_value(msg, "json")
                elif "/get/fault_state" in msg.topic:
                    self._validate_value(msg, int, [(0, 2)])
                elif "/get/fault_str" in msg.topic:
                    self._validate_value(msg, str)
                else:
                    self.__unknown_topic(msg)
            else:
                # hier kommen auch noch alte Topics ohne json-Format an.
                # MainLogger().error("Unbekanntes set-Topic: "+str(msg.topic)+", "+
                # str(json.loads(str(msg.payload.decode("utf-8")))))
                Pub().pub(msg.topic, "")
        except Exception:
            MainLogger().exception("Fehler im setdata-Modul")

    def process_command_topic(self, msg):
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
            else:
                self.__unknown_topic(msg)
        except Exception:
            MainLogger().exception("Fehler im setdata-Modul")
