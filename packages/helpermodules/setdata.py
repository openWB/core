""" Modul, um die Daten vom Broker zu erhalten.
"""

import copy
import json
import paho.mqtt.client as mqtt
import re

from . import log
from . import pub
from . import subdata

class setData():
 
    def __init__(self, event_ev_template, event_charge_template, event_cp_config):
        self.event_ev_template = event_ev_template
        self.event_charge_template = event_charge_template
        self.event_cp_config = event_cp_config
        self.heartbeat = False

    def set_data(self):
        """ abonniert alle set-Topics.
        """
        mqtt_broker_ip = "localhost"
        client = mqtt.Client("openWB-mqttsub-" + self.getserial())
        # ipallowed='^[0-9.]+$'
        # nameallowed='^[a-zA-Z ]+$'
        # namenumballowed='^[0-9a-zA-Z ]+$'

        client.on_connect = self.on_connect
        client.on_message = self.on_message

        client.connect(mqtt_broker_ip, 1886)
        client.loop_forever()
        client.disconnect()

    def getserial(self):
        """ Extract serial from cpuinfo file
        """
        with open('/proc/cpuinfo','r') as f:
            for line in f:
                if line[0:6] == 'Serial':
                    return line[10:26]
            return "0000000000000000"

    def on_connect(self, client, userdata, flags, rc):
        """ connect to broker and subscribe to set topics
        """
        client.subscribe("openWB/set/#", 2)

    def on_message(self, client, userdata, msg):
        """ ruft die Funktion auf, um das Topic zu verarbeiten. Wenn die Topics mit Locking verarbeitet werden, wird gewartet, bis das Locking aufgehoben wird.

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
        log.message_mqtt_log(str(msg.topic), str(msg.payload.decode("utf-8")))
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

    def _validate_value(self, msg, data_type, ranges = None, collection = None, pub_json = False):
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
            gibt an, ob das Topic von openWB/set/.. an openWB/.. gepublished werden soll oder ein json-Objekt, dass mehrere Daten enthält.
        """
        valid = False
        try:
            if msg.payload:
                value = json.loads(str(msg.payload.decode("utf-8")))
                if data_type == None or data_type == "json":
                    # Wenn kein gültiges json-Objekt übergeben worden wäre, wäre bei loads eine Exception aufgetreten.
                    valid = True
                elif collection != None:
                        if self._validate_collection_value(msg, data_type, ranges, collection) == True:
                            valid = True
                elif data_type == str:
                    if isinstance(value, str) == True:
                        valid = True
                    else:
                        log.message_debug_log("error", "Payload ungueltig: Topic "+str(msg.topic)+", Payload "+str(value)+" sollte ein String sein.")
                elif data_type == int or data_type == float:
                    if self._validate_min_max_value(value, msg, data_type, ranges) == True:
                        valid = True
                
                if valid == True:
                    if pub_json == False:
                        pub.pub(msg.topic.replace('set/', '', 1), value)
                        pub.pub(msg.topic, "")
                    else:
                        # aktuelles json-Objekt liegt in subdata
                        index = re.search('(?!/)([0-9]*)(?=/|$)', msg.topic).group()
                        if "charge_template" in msg.topic:
                            event = self.event_charge_template
                            if "ct"+str(index) in subdata.subData.ev_charge_template_data:
                                template = copy.deepcopy(subdata.subData.ev_charge_template_data["ct"+str(index)].data)
                            else:
                                template = {}
                        elif "ev_template" in msg.topic:
                            event = self.event_ev_template
                            if "et"+str(index) in subdata.subData.ev_template_data:
                                template = copy.deepcopy(subdata.subData.ev_template_data["et"+str(index)].data)
                            else:
                                template = {}
                        elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/config.*$", msg.topic) != None:
                            event = self.event_cp_config
                            if "cp"+str(index) in subdata.subData.cp_data:
                                template = copy.deepcopy(subdata.subData.cp_data["cp"+str(index)].data["config"])
                            else:
                                template = {}
                        # Wert, der aktualisiert werden soll, erstellen/finden und updaten
                        if event == self.event_cp_config:
                            key_list = msg.topic.split("/")[5:]
                        else:
                            key_list = msg.topic.split("/")[6:]
                        self._change_key(template, key_list, value)
                        # publish
                        index_pos = re.search('(?!/)([0-9]*)(?=/|$)', msg.topic).end()
                        if event == self.event_cp_config:
                            topic = msg.topic[:index_pos]+"/config"
                        else:
                            topic = msg.topic[:index_pos]
                        topic = topic.replace('set/', '', 1)
                        pub.pub(topic, template)
                        pub.pub(msg.topic, "")
                        event.clear()
                else:
                    pub.pub(msg.topic, "")
        except Exception as e:
            log.exception_logging(e)
            pub.pub(msg.topic, "")

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
        except Exception as e:
            log.exception_logging(e)

    def _validate_collection_value(self, msg, data_type, ranges = None, collection = None):
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
            if isinstance(value, list) == True:
                for item in value:
                    if self._validate_min_max_value(item, msg, data_type, ranges) == False:
                        break
                else:
                    valid = True
            elif isinstance(value, dict) == True:
                for item in value.values():
                    if self._validate_min_max_value(item, msg, data_type, ranges) == False:
                        break
                else:
                    valid = True
            else:
                log.message_debug_log("error", "Payload ungueltig: Topic "+str(msg.topic)+", Payload "+str(value)+" sollte eine Kollektion vom Typ "+str(collection)+" sein.")
            return valid
        except Exception as e:
            log.exception_logging(e)

    def _validate_min_max_value(self, value, msg, data_type, ranges = None):
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
            # Wenn es ein Float erwartet wird, kann auch ein Int akzeptiert werden. Da dies automatisch umgewandelt wird, falls erfoderlich.
            if isinstance(value, data_type) == True or (data_type == float and isinstance(value, int) == True):
                if ranges != None:
                    for range in ranges:
                        if range[0] != None and range[1] != None:
                            if range[0] <= value <= range[1]:
                                break
                        elif range[0] != None:
                            if value >= range[0]:
                                break
                        elif range[1] != None:
                            if value <= range[1]:
                                break
                    else:
                        log.message_debug_log("error", "Payload ungueltig: Topic "+str(msg.topic)+", Payload "+str(value)+" liegt in keinem der angegebenen Wertebereiche.")
                        valid = False
            else:
                if data_type == int:
                    log.message_debug_log("error", "Payload ungueltig: Topic "+str(msg.topic)+", Payload "+str(value)+" sollte ein Int sein.")
                elif data_type == float:
                    log.message_debug_log("error", "Payload ungueltig: Topic "+str(msg.topic)+", Payload "+str(value)+" sollte ein Float sein.")
                valid = False
            return valid
        except Exception as e:
            log.exception_logging(e)
 
    def process_vehicle_topic(self, msg):
        """ Handler für die EV-Topics

         Parameters
        ----------
        msg:
            enthält Topic und Payload
        """
        try:
            if re.search("^openWB/set/vehicle/[0-9]+/name$", msg.topic) != None:
                self._validate_value(msg, str)
            elif (re.search("^openWB/set/vehicle/[0-9]+/soc/config/request_interval_charging$", msg.topic) != None or
                    re.search("^openWB/set/vehicle/[0-9]+/soc/config/reques_interval_not_charging$", msg.topic) != None):
                self._validate_value(msg, int, [(0, None)])
            elif (re.search("^openWB/set/vehicle/[0-9]+/soc/config/request_only_plugged$", msg.topic) != None or
                    re.search("^openWB/set/vehicle/[0-9]+/soc/config/configured$", msg.topic) != None or
                    re.search("^openWB/set/vehicle/[0-9]+/soc/config/manual$", msg.topic) != None):
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/vehicle/[0-9]+/soc/get/fault_state$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 2)])
            elif re.search("^openWB/set/vehicle/[0-9]+/soc/get/fault_str$", msg.topic) != None:
                self._validate_value(msg, str)
            elif re.search("^openWB/set/vehicle/[0-9]+/tag_id$", msg.topic) != None:
                self._validate_value(msg, str, collection=list)
            elif (re.search("^openWB/set/vehicle/[0-9]+/charge_template$", msg.topic) != None or
                    re.search("^openWB/set/vehicle/[0-9]+/ev_template$", msg.topic) != None):
                self._validate_value(msg, int, [(0, None)])
            elif re.search("^openWB/set/vehicle/[0-9]+/get/soc_timestamp$", msg.topic) != None:
                self._validate_value(msg, int, [(0, None)])
            elif re.search("^openWB/set/vehicle/[0-9]+/get/soc$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 100)])
            elif re.search("^openWB/set/vehicle/[0-9]+/set/ev_template$", msg.topic) != None:
                self._validate_value(msg, "json")
            elif re.search("^openWB/set/vehicle/[0-9]+/control_parameter/required_current$", msg.topic) != None:
                self._validate_value(msg, float, [(6, 32), (0, 0)])
            elif re.search("^openWB/set/vehicle/[0-9]+/control_parameter/phases$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 3)])
            elif (re.search("^openWB/set/vehicle/[0-9]+/control_parameter/submode$", msg.topic) != None or
                    re.search("^openWB/set/vehicle/[0-9]+/control_parameter/chargemode$", msg.topic) != None):
                self._validate_value(msg, str)
            elif re.search("^openWB/set/vehicle/[0-9]+/control_parameter/prio$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)])
            elif (re.search("^openWB/set/vehicle/[0-9]+/control_parameter/timestamp_switch_on_off$", msg.topic) != None or
                    re.search("^openWB/set/vehicle/[0-9]+/control_parameter/timestamp_auto_phase_switch$", msg.topic) != None or
                    re.search("^openWB/set/vehicle/[0-9]+/control_parameter/timestamp_perform_phase_switch$", msg.topic) != None):
                self._validate_value(msg, str)
            elif "openWB/set/vehicle/template" in msg.topic:
                self._subprocess_vehicle_chargemode_topic(msg)
            else:
                log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))
                pub.pub(msg.topic, "")
        except Exception as e:
            log.exception_logging(e)

    def _subprocess_vehicle_chargemode_topic(self, msg):
        """ Handler für die EV-Chargemode-Template-Topics
        Parameters
        ----------
        msg:
            enthält Topic und Payload
        """
        try:
            if re.search("^openWB/set/vehicle/template/charge_template/[0-9]+/name$", msg.topic) != None:
                self._validate_value(msg, str, pub_json = True)
            elif (re.search("^openWB/set/vehicle/template/charge_template/[0-9]+/load_default$", msg.topic) != None or
                    re.search("^openWB/set/vehicle/template/charge_template/[0-9]+/disable_after_unplug$", msg.topic) != None or
                    re.search("^openWB/set/vehicle/template/charge_template/[0-9]+/prio$", msg.topic) != None):
                self._validate_value(msg, int, [(0, 1)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[0-9]+/chargemode/selected$", msg.topic) != None:
                self._validate_value(msg, str, pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[0-9]+/chargemode/instant_charging/current$", msg.topic) != None:
                self._validate_value(msg, int, [(6, 32)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[0-9]+/chargemode/instant_charging/limit/selected$", msg.topic) != None:
                self._validate_value(msg, str, pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[0-9]+/chargemode/instant_charging/limit/soc$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 100)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[0-9]+/chargemode/instant_charging/limit/amount$", msg.topic) != None:
                self._validate_value(msg, int, [(2, 100)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[0-9]+/chargemode/pv_charging/feed_in_limit$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[0-9]+/chargemode/pv_charging/min_current$", msg.topic) != None:
                self._validate_value(msg, int, [(0,0), (6, 16)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[0-9]+/chargemode/pv_charging/min_soc$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 100)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[0-9]+/chargemode/pv_charging/min_soc_current$", msg.topic) != None:
                self._validate_value(msg, int, [(6, 32)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[0-9]+/chargemode/pv_charging/max_soc$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 100)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[0-9]+/chargemode/scheduled_charging/[0-9]+/active$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[0-9]+/chargemode/scheduled_charging$", msg.topic) != None:
                self._validate_value(msg, "json", pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[0-9]+/time_charging/active$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[0-9]+/time_charging/plans$", msg.topic) != None:
                self._validate_value(msg, "json", pub_json = True)
            elif re.search("^openWB/set/vehicle/template/ev_template/[0-9]+/name$", msg.topic) != None:
                self._validate_value(msg, str, pub_json = True)
            elif re.search("^openWB/set/vehicle/template/ev_template/[0-9]+/average_consump$", msg.topic) != None:
                self._validate_value(msg, float, [(0, None)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/ev_template/[0-9]+/battery_capacity$", msg.topic) != None:
                self._validate_value(msg, int, [(0, None)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/ev_template/[0-9]+/max_phases$", msg.topic) != None:
                self._validate_value(msg, int, [(1, 3)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/ev_template/[0-9]+/min_current$", msg.topic) != None:
                self._validate_value(msg, int, [(6, 32)], pub_json = True)
            elif (re.search("^openWB/set/vehicle/template/ev_template/[0-9]+/max_current_one_phase$", msg.topic) != None or
                    re.search("^openWB/set/vehicle/template/ev_template/[0-9]+/max_current_multi_phases$", msg.topic) != None):
                self._validate_value(msg, int, [(0, 0), (6, 32)], pub_json = True)
            elif (re.search("^openWB/set/vehicle/template/ev_template/[0-9]+/control_pilot_interruption$", msg.topic) != None or
                    re.search("^openWB/set/vehicle/template/ev_template/[0-9]+/prevent_switch_stop$", msg.topic) != None):
                self._validate_value(msg, int, [(0, 1)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/ev_template/[0-9]+/control_pilot_interruption_duration$", msg.topic) != None:
                self._validate_value(msg, int, [(4, 15)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/ev_template/[0-9]+/nominal_difference$", msg.topic) != None:
                self._validate_value(msg, float, [(0, 4)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/ev_template/[0-9]+/phase_switch_pause$", msg.topic) != None:
                self._validate_value(msg, int, [(2, 150)], pub_json = True)
            else:
                log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))
                pub.pub(msg.topic, "")
        except Exception as e:
            log.exception_logging(e)

    def process_chargepoint_topic(self, msg):
        """ Handler für die Ladepunkt-Topics

         Parameters
        ----------

        msg:
            enthält Topic und Payload
        """
        try:
            if (re.search("^openWB/set/chargepoint/get/counter_all$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/get/power_all$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/get/daily_yield$", msg.topic) != None):
                self._validate_value(msg, float, [(0, None)])
            elif (re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/charging_ev$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/charging_ev_prev$", msg.topic) != None):
                self._validate_value(msg, int, [(-1, None)])
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/current$", msg.topic) != None:
                self._validate_value(msg, float, [(6, 32), (0, 0)])
            elif (re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/energy_to_charge$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/required_power$", msg.topic) != None):
                self._validate_value(msg, float, [(0, None)])
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/phases_to_use$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 3)])
            elif (re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/manual_lock$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/perform_control_pilot_interruption$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/perform_phase_switch$", msg.topic) != None):
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/autolock_state$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 4)])
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/rfid$", msg.topic) != None:
                self._validate_value(msg, str)
            elif (re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/log/time_charged$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/log/chargemode_log_entry$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[0-9]+/set/plug_time$", msg.topic) != None):
                self._validate_value(msg, str)
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/change_ev_permitted$", msg.topic) != None:
                self._validate_value(msg, "json")
            elif (re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/log/range_charged$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/log/counter$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/log/charged_since_mode_switch$", msg.topic) != None or 
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/log/charged_since_plugged_counter$", msg.topic) != None or 
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/log/counter_at_mode_switch$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/log/counter_at_plugtime$", msg.topic) != None):
                self._validate_value(msg, float, [(0, None)])
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/log/timestamp_start_charging$", msg.topic) != None:
                self._validate_value(msg, str)
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/config$", msg.topic) != None:
                self._validate_value(msg, "json")
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/ev$", msg.topic) != None:
                self._validate_value(msg, int, [(0, None)], pub_json = True)
            elif (re.search("^openWB/set/chargepoint/[1-9][0-9]*/get/voltage$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/get/current$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/get/power_factor$", msg.topic) != None):
                self._validate_value(msg, float, [(0, None)], collection=list)
            elif (re.search("^openWB/set/chargepoint/[1-9][0-9]*/get/daily_yield$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/get/power_all$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/get/counter$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/get/charged_since_plugged_counter$", msg.topic) != None):
                self._validate_value(msg, float, [(0, None)])
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/get/phases_in_use", msg.topic) != None:
                self._validate_value(msg, int, [(0, 3)])
            elif (re.search("^openWB/set/chargepoint/[1-9][0-9]*/get/charge_state$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/get/plug_state$", msg.topic) != None):
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/get/fault_state$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 2)])
            elif (re.search("^openWB/set/chargepoint/[0-9]+/get/fault_str$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[0-9]+/get/state_str$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[0-9]+/get/heartbeat$", msg.topic) != None):
                self._validate_value(msg, str)
            elif re.search("^openWB/set/chargepoint/[0-9]+/get/read_tag$", msg.topic) != None:
                self._validate_value(msg, "json")
            elif (re.search("^openWB/set/chargepoint/template/[1-9][0-9]*/autolock/active$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/template/[1-9][0-9]*/autolock/wait_for_charging_end$", msg.topic) != None):
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/chargepoint/template/[1-9][0-9]*/autolock/[1-9][0-9]*/active$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)])
            elif (re.search("^openWB/set/chargepoint/template/[1-9][0-9]*/autolock/[1-9][0-9]*/frequency/selected$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/template/[1-9][0-9]*/autolock/[1-9][0-9]*/frequency/once$", msg.topic) != None):
                self._validate_value(msg, str)
            elif re.search("^openWB/set/chargepoint/template/[1-9][0-9]*/autolock/[1-9][0-9]*/frequency/weekly$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)], collection=list)
            elif re.search("^openWB/set/chargepoint/template/[1-9][0-9]*/autolock/[1-9][0-9]*/time$", msg.topic) != None:
                self._validate_value(msg, str, collection=list)
            elif re.search("^openWB/set/chargepoint/template/[1-9][0-9]*/rfid_enabling$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/chargepoint/template/[1-9][0-9]*/valid_tags$", msg.topic) != None:
                self._validate_value(msg, str, collection=list)
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/get/rfid$", msg.topic) != None:
                ### isss Anpassung muss noch in die nightly
                pub.pub(msg.topic, "")
            else:
                log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))
                pub.pub(msg.topic, "")
        except Exception as e:
            log.exception_logging(e)

    def process_pv_topic(self, msg):
        """ Handler für die PV-Topics

         Parameters
        ----------

        msg:
            enthält Topic und Payload
        """
        try:
            if re.search("^openWB/set/pv/config/configured$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)])
            elif (re.search("^openWB/set/pv/get/daily_yield$", msg.topic) != None or
                    re.search("^openWB/set/pv/get/monthly_yield$", msg.topic) != None or
                    re.search("^openWB/set/pv/get/yearly_yield$", msg.topic) != None):
                self._validate_value(msg, float, [(0, None)])
            elif re.search("^openWB/set/pv/get/counter$", msg.topic) != None:
                self._validate_value(msg, int, [(0, None)])
            elif re.search("^openWB/set/pv/get/power$", msg.topic) != None:
                self._validate_value(msg, int, [(None, 0)])
            elif (re.search("^openWB/set/pv/set/overhang_power_left$", msg.topic) != None or
                    re.search("^openWB/set/pv/set/reserved_evu_overhang$", msg.topic) != None or
                    re.search("^openWB/set/pv/set/released_evu_overhang$", msg.topic) != None):
                self._validate_value(msg, float)
            elif re.search("^openWB/set/pv/set/available_power$", msg.topic) != None:
                self._validate_value(msg, float)
            elif re.search("^openWB/set/pv/[1-9][0-9]*/config$", msg.topic) != None:
                self._validate_value(msg, "json")
            elif re.search("^openWB/set/pv/[1-9][0-9]*/get/fault_state$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 2)])
            elif re.search("^openWB/set/pv/[1-9][0-9]*/get/fault_str$", msg.topic) != None:
                self._validate_value(msg, str)
            elif (re.search("^openWB/set/pv/[1-9][0-9]*/get/daily_yield$", msg.topic) != None or
                    re.search("^openWB/set/pv/[1-9][0-9]*/get/monthly_yield$", msg.topic) != None or
                    re.search("^openWB/set/pv/[1-9][0-9]*/get/yearly_yield$", msg.topic) != None or
                    re.search("^openWB/set/pv/[1-9][0-9]*/get/energy$", msg.topic) != None):
                self._validate_value(msg, float, [(0, None)])
            elif re.search("^openWB/set/pv/[1-9][0-9]*/get/counter$", msg.topic) != None:
                self._validate_value(msg, int, [(0, None)])
            elif re.search("^openWB/set/pv/[1-9][0-9]*/get/power$", msg.topic) != None:
                self._validate_value(msg, int, [(None, 0)])
            elif re.search("^openWB/set/pv/[1-9][0-9]*/get/actual_power_phase$", msg.topic) != None:
                self._validate_value(msg, float, [(0, None)], collection=list)
            else:
                log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))
                pub.pub(msg.topic, "")
        except Exception as e:
            log.exception_logging(e)

    def process_bat_topic(self, msg):
        """ Handler für die Hausspeicher-Topics

         Parameters
        ----------

        msg:
            enthält Topic und Payload
        """
        try:
            if (re.search("^openWB/set/bat/config/configured$", msg.topic) != None or 
                    re.search("^openWB/set/bat/set/switch_on_soc_reached$", msg.topic) != None or
                    re.search("^openWB/set/bat/set/hybrid_system_detected$", msg.topic) != None):
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/bat/set/charging_power_left$", msg.topic) != None:
                self._validate_value(msg, int)
            elif re.search("^openWB/set/bat/get/soc$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 100)])
            elif re.search("^openWB/set/bat/get/power$", msg.topic) != None:
                self._validate_value(msg, int)
            elif (re.search("^openWB/set/bat/get/imported$", msg.topic) != None or
                    re.search("^openWB/set/bat/get/exported$", msg.topic) != None or
                    re.search("^openWB/set/bat/get/daily_yield_export$", msg.topic) != None or
                    re.search("^openWB/set/bat/get/daily_yield_import$", msg.topic) != None):
                self._validate_value(msg, float, [(0, None)])
            elif re.search("^openWB/set/bat/[1-9][0-9]*/config$", msg.topic) != None:
                self._validate_value(msg, "json")
            elif re.search("^openWB/set/bat/[1-9][0-9]*/get/power$", msg.topic) != None:
                self._validate_value(msg, float)
            elif (re.search("^openWB/set/bat/[1-9][0-9]*/get/imported$", msg.topic) != None or
                    re.search("^openWB/set/bat/[1-9][0-9]*/get/exported$", msg.topic) != None or
                    re.search("^openWB/set/bat/[1-9][0-9]*/get/daily_yield_export$", msg.topic) != None or
                    re.search("^openWB/set/bat/[1-9][0-9]*/get/daily_yield_import$", msg.topic) != None):
                self._validate_value(msg, float, [(0, None)])
            elif re.search("^openWB/set/bat/[1-9][0-9]*/get/soc$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 100)])
            elif re.search("^openWB/set/bat/[1-9][0-9]*/get/fault_state$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 2)])
            elif re.search("^openWB/set/bat/[1-9][0-9]*/get/fault_str$", msg.topic) != None:
                self._validate_value(msg, str)
            else:
                log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))
                pub.pub(msg.topic, "")
        except Exception as e:
            log.exception_logging(e)

    def process_general_topic(self, msg):
        """ Handler für die Allgemeinen-Topics

         Parameters
        ----------

        msg:
            enthält Topic und Payload
        """
        try:
            if re.search("^openWB/set/general/extern$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/general/control_interval$", msg.topic) != None:
                self._validate_value(msg, int, [(10, 10), (20, 20), (60, 60)])
            elif re.search("^openWB/set/general/external_buttons_hw$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/general/chargemode_config/individual_mode$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/general/chargemode_config/unbalanced_load$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/general/chargemode_config/unbalanced_load_limit$", msg.topic) != None:
                self._validate_value(msg, int, [(10, 32)])
            elif (re.search("^openWB/set/general/chargemode_config/pv_charging/feed_in_yield$", msg.topic) != None or 
                    re.search("^openWB/set/general/chargemode_config/pv_charging/switch_on_threshold$", msg.topic) != None or
                    re.search("^openWB/set/general/chargemode_config/pv_charging/switch_on_delay$", msg.topic) != None or
                    re.search("^openWB/set/general/chargemode_config/pv_charging/switch_off_threshold$", msg.topic) != None or
                    re.search("^openWB/set/general/chargemode_config/pv_charging/switch_off_delay$", msg.topic) != None):
                self._validate_value(msg, int, [(0, None)])
            elif re.search("^openWB/set/general/chargemode_config/pv_charging/phase_switch_delay$", msg.topic) != None:
                self._validate_value(msg, int, [(1, 15)])
            elif re.search("^openWB/set/general/chargemode_config/pv_charging/control_range$", msg.topic) != None:
                self._validate_value(msg, int, collection=list)
            elif ((re.search("^openWB/set/general/chargemode_config/pv_charging/phases_to_use$", msg.topic) != None or
                    re.search("^openWB/set/general/chargemode_config/scheduled_charging/phases_to_use$", msg.topic) != None)):
                self._validate_value(msg, int, [(0, 0), (1, 1), (3, 3)])
            elif re.search("^openWB/set/general/chargemode_config/pv_charging/bat_prio$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)])
            elif (re.search("^openWB/set/general/chargemode_config/pv_charging/switch_on_soc$", msg.topic) != None or
                    re.search("^openWB/set/general/chargemode_config/pv_charging/switch_off_soc$", msg.topic) != None or
                    re.search("^openWB/set/general/chargemode_config/pv_charging/rundown_soc$", msg.topic) != None):
                self._validate_value(msg, int, [(0, 100)])
            elif (re.search("^openWB/set/general/chargemode_config/pv_charging/rundown_power$", msg.topic) != None or
                    re.search("^openWB/set/general/chargemode_config/pv_charging/charging_power_reserve$", msg.topic) != None):
                self._validate_value(msg, int, [(0, None)])
            elif re.search("^openWB/set/general/chargemode_config/[a-z,_]+/phases_to_use$", msg.topic) != None:
                self._validate_value(msg, int, [(1, 1), (3, 3)])
            elif (re.search("^openWB/set/general/grid_protection_configured$", msg.topic) != None or
                    re.search("^openWB/set/general/grid_protection_active$", msg.topic) != None or
                    re.search("^openWB/set/general/mqtt_bridge$", msg.topic) != None):
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/general/grid_protection_timestamp$", msg.topic) != None:
                self._validate_value(msg, str)
            elif re.search("^openWB/set/general/grid_protection_random_stop$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 90)])
            elif re.search("^openWB/set/general/notifications/selected$", msg.topic) != None:
                self._validate_value(msg, str)
            elif (re.search("^openWB/set/general/notifications/start_charging$", msg.topic) != None or
                    re.search("^openWB/set/general/notifications/stop_charging$", msg.topic) != None or
                    re.search("^openWB/set/general/notifications/plug$", msg.topic) != None or
                    re.search("^openWB/set/general/notifications/smart_home$", msg.topic) != None):
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/general/price_kwh$", msg.topic) != None:
                self._validate_value(msg, float, [(0, 99.99)])
            elif re.search("^openWB/set/general/range_unit$", msg.topic) != None:
                self._validate_value(msg, str)
            elif (re.search("^openWB/set/general/ripple_control_receiver/configured$", msg.topic) != None or
                    re.search("^openWB/set/general/ripple_control_receiver/r1_active$", msg.topic) != None or
                    re.search("^openWB/set/general/ripple_control_receiver/r2_active$", msg.topic) != None):
                self._validate_value(msg, int, [(0, 1)])
            else:
                log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))
                pub.pub(msg.topic, "")
        except Exception as e:
            log.exception_logging(e)

    def process_optional_topic(self, msg):
        """ Handler für die Optionalen-Topics

         Parameters
        ----------

        msg:
            enthält Topic und Payload
        """
        try:
            if re.search("^openWB/set/optional/load_sharing/active$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/optional/load_sharing/max_current$", msg.topic) != None:
                self._validate_value(msg, int, [(16, 32)])
            elif re.search("^openWB/set/optional/et/active$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/optional/et/get/price_list$", msg.topic) != None:
                self._validate_value(msg, "json")
            elif re.search("^openWB/set/optional/et/get/price$", msg.topic) != None:
                self._validate_value(msg, float)
            elif re.search("^openWB/set/optional/et/get/source$", msg.topic) != None:
                self._validate_value(msg, str)
            elif re.search("^openWB/set/optional/et/config/max_price$", msg.topic) != None:
                self._validate_value(msg, float)
            elif re.search("^openWB/set/optional/et/config/provider$", msg.topic) != None:
                self._validate_value(msg, "json")
            elif re.search("^openWB/set/optional/rfid/active$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)])
            else:
                log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))
                pub.pub(msg.topic, "")
        except Exception as e:
            log.exception_logging(e)

    def process_counter_topic(self, msg):
        """ Handler für die Zähler-Topics

         Parameters
        ----------

        msg:
            enthält Topic und Payload
        """
        try:
            if re.search("^openWB/set/counter/set/loadmanagement$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/counter/set/invalid_home_consumption$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 3)])
            elif (re.search("^openWB/set/counter/set/home_consumption$", msg.topic) != None or
                    re.search("^openWB/set/counter/set/daily_yield_home_consumption$", msg.topic) != None):
                self._validate_value(msg, float, [(0, None)])
            elif re.search("^openWB/set/counter/get/hierarchy$", msg.topic) != None:
                self._validate_value(msg, None)
            elif re.search("^openWB/set/counter/[0-9]+/set/consumption_left$", msg.topic) != None:
                self._validate_value(msg, float)
            elif re.search("^openWB/set/counter/[0-9]+/set/current_left$", msg.topic) != None:
                self._validate_value(msg, float, [(0, None)], collection=list)
            elif re.search("^openWB/set/counter/[0-9]+/config/selected$", msg.topic) != None:
                self._validate_value(msg, str)
            elif re.search("^openWB/set/counter/[0-9]+/module$", msg.topic) != None:
                self._validate_value(msg, "json")
            elif (re.search("^openWB/set/counter/[0-9]+/module/simulation/present_power_all$", msg.topic) != None or
                    re.search("^openWB/set/counter/[0-9]+/module/simulation/present_imported$", msg.topic) != None or
                    re.search("^openWB/set/counter/[0-9]+/module/simulation/present_exported$", msg.topic) != None):
                self._validate_value(msg, float)
            elif re.search("^openWB/set/counter/[0-9]+/module/simulation/sim_timestamp$", msg.topic) != None:
                self._validate_value(msg, str)
            elif re.search("^openWB/set/counter/[0-9]+/config/max_current$", msg.topic) != None:
                self._validate_value(msg, int, [(7, 1500)], collection = list)
            elif re.search("^openWB/set/counter/[0-9]+/config/max_consumption$", msg.topic) != None:
                self._validate_value(msg, int, [(2000, 1000000)])
            elif re.search("^openWB/set/counter/[0-9]+/get/power_all$", msg.topic) != None:
                self._validate_value(msg, float)
            elif re.search("^openWB/set/counter/[0-9]+/get/current$", msg.topic) != None:
                self._validate_value(msg, float, collection=list)
            elif (re.search("^openWB/set/counter/[0-9]+/get/voltage$", msg.topic) != None or
                    re.search("^openWB/set/counter/[0-9]+/get/power_phase$", msg.topic) != None or
                    re.search("^openWB/set/counter/[0-9]+/get/power_factor$", msg.topic) != None):
                self._validate_value(msg, float, [(0, None)], collection=list)
            elif (re.search("^openWB/set/counter/[0-9]+/get/power_average$", msg.topic) != None
                    or re.search("^openWB/set/counter/[0-9]+/get/unbalanced_load$", msg.topic) != None
                    or re.search("^openWB/set/counter/[0-9]+/get/frequency$", msg.topic) != None
                    or re.search("^openWB/set/counter/[0-9]+/get/daily_yield_export$", msg.topic) != None
                    or re.search("^openWB/set/counter/[0-9]+/get/daily_yield_import$", msg.topic) != None
                    or re.search("^openWB/set/counter/[0-9]+/get/imported$", msg.topic) != None
                    or re.search("^openWB/set/counter/[0-9]+/get/exported$", msg.topic) != None):
                self._validate_value(msg, float, [(0, None)])
            elif re.search("^openWB/set/counter/[0-9]/get/fault_state$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 2)])
            elif re.search("^openWB/set/counter/[0-9]/get/fault_str$", msg.topic) != None:
                self._validate_value(msg, str)
            else:
                log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))
                pub.pub(msg.topic, "")
        except Exception as e:
            log.exception_logging(e)

    def process_log_topic(self, msg):
        """Handler für die Log-Topics

         Parameters
        ----------

        msg:
            enthält Topic und Payload
        """
        try:
            if (re.search("^openWB/set/log/request$", msg.topic) != None or
                    re.search("^openWB/set/log/data$", msg.topic) != None):
                self._validate_value(msg, "json")
            else:
                log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))
                pub.pub(msg.topic, "")
        except Exception as e:
            log.exception_logging(e)

    def process_graph_topic(self, msg):
        """Handler für die Graph-Topics

         Parameters
        ----------
        msg:
            enthält Topic und Payload
        """
        try:
            if (re.search("^openWB/set/graph/alllivevaluesJson[0-9]*$", msg.topic) != None or
                    re.search("^openWB/set/graph/lastlivevaluesJson$", msg.topic) != None):
                self._validate_value(msg, "json")
            else:
                log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))
                pub.pub(msg.topic, "")
        except Exception as e:
            log.exception_logging(e)

    def process_system_topic(self, msg):
        """Handler für die System-Topics

         Parameters
        ----------
        msg:
            enthält Topic und Payload
        """
        try:
            if re.search("^openWB/set/system/lastlivevaluesJson$", msg.topic) != None:
                self._validate_value(msg, "json")
            elif (re.search("^openWB/set/system/perform_update$", msg.topic) != None or
                    re.search("^openWB/set/system/update_in_progress$", msg.topic) != None):
                self._validate_value(msg, int, [(0, 1)])
            else:
                # hier kommen auch noch alte Topics ohne json-Format an.
                #log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))
                pub.pub(msg.topic, "")
        except Exception as e:
            log.exception_logging(e)