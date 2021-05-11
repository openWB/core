""" Modul, um die Daten vom Broker zu erhalten.
"""

import copy
import json
import paho.mqtt.client as mqtt
import re

import log
import pub
import subdata

class setData():
 
    def __init__(self):
        pass

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
        client.message_callback_add("openWB/set/vehicle/#", self.process_vehicle_topic)
        client.message_callback_add("openWB/set/chargepoint/#", self.process_chargepoint_topic)
        client.message_callback_add("openWB/set/pv/#", self.process_pv_topic)
        client.message_callback_add("openWB/set/bat/#", self.process_bat_topic)
        client.message_callback_add("openWB/set/general/#", self.process_general_topic)
        client.message_callback_add("openWB/set/optional/#", self.process_optional_topic)
        client.message_callback_add("openWB/set/counter/#", self.process_counter_topic)
        # client.message_callback_add("openWB/set/graph/#", self.process_graph_topic)
        # client.message_callback_add("openWB/set/smarthome/#", self.processSmarthomeTopic)

        client.connect(mqtt_broker_ip, 1883)
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
        """ wartet auf eingehende Topics.
        """
        #self.log_mqtt()
        #print("Unknown topic: "+msg.topic+", "+str(msg.payload.decode("utf-8")))

    def _validate_value(self, msg, data_type, ranges = None, collection = None, pub_json = False):
        """ prüft, ob der Wert vom angegebenen Typ ist.

        Parameter
        ---------
        msg:
            Broker-Nachricht
        data_type: float, int, str, None
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
                if data_type == None:
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
                    else:
                        # aktuelles json-Objekt liegt in subdata
                        index = re.search('(?!/)([0-9]*)(?=/|$)', msg.topic).group()
                        if "charge_template" in msg.topic:
                            if "ct"+str(index) in subdata.subData.ev_charge_template_data:
                                template = copy.deepcopy(subdata.subData.ev_charge_template_data["ct"+str(index)].data)
                            else:
                                template = {}
                        elif "ev_template" in msg.topic:
                            if "et"+str(index) in subdata.subData.ev_template_data:
                                template = copy.deepcopy(subdata.subData.ev_template_data["et"+str(index)].data)
                            else:
                                template = {}
                        # Wert, der aktualisiert werden soll, erstellen/finden und updaten
                        key_list = msg.topic.split("/")[6:]
                        self._change_key(template, key_list, value)
                        # publish
                        index_pos = re.search('(?!/)([0-9]*)(?=/|$)', msg.topic).start()
                        topic = msg.topic[:index_pos+1]
                        topic = topic.replace('set/', '', 1)
                        pub.pub(topic, template)
                pub.pub(msg.topic, "")
        except Exception as e:
            log.exception_logging(e)

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
        if len(key_list) == 1:
            next_level[key_list[0]] = value
        else:
            if key_list[0] not in next_level:
                next_level[key_list[0]] = {}
            next_key = key_list[0]
            key_list.pop(0)
            self._change_key(next_level[next_key], key_list, value)

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
 
    def process_vehicle_topic(self, client, userdata, msg):
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
            elif re.search("^openWB/set/vehicle/[0-9]+/match_ev/selected$", msg.topic) != None:
                self._validate_value(msg, str)
            elif re.search("^openWB/set/vehicle/[0-9]+/match_ev/tag_id$", msg.topic) != None:
                self._validate_value(msg, int, [(0, None)])
            elif re.search("^openWB/set/vehicle/[0-9]+/match_ev/inactive$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)])
            elif (re.search("^openWB/set/vehicle/[0-9]+/charge_template$", msg.topic) != None or
                    re.search("^openWB/set/vehicle/[0-9]+/ev_template$", msg.topic) != None):
                self._validate_value(msg, int, [(1, None)])
            elif (re.search("^openWB/set/vehicle/[0-9]+/get/daily_counter$", msg.topic) != None or
                    re.search("^openWB/set/vehicle/[0-9]+/get/range_charged$", msg.topic) != None or
                    re.search("^openWB/set/vehicle/[0-9]+/get/counter$", msg.topic) != None or
                    re.search("^openWB/set/vehicle/[0-9]+/get/charged_since_plugged_counter$", msg.topic) != None or 
                    re.search("^openWB/set/vehicle/[0-9]+/get/counter_at_plugtime$", msg.topic) != None or
                    re.search("^openWB/set/vehicle/[0-9]+/get/soc_timestamp$", msg.topic) != None):
                self._validate_value(msg, int, [(0, None)])
            elif re.search("^openWB/set/vehicle/[0-9]+/get/soc$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 100)])
            elif re.search("^openWB/set/vehicle/[0-9]+/control_parameter/required_current$", msg.topic) != None:
                self._validate_value(msg, int, [(6, 32), (0, 0)])
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
            if re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/name$", msg.topic) != None:
                self._validate_value(msg, str, pub_json = True)
            elif (re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/load_default$", msg.topic) != None or
                    re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/disable_after_unplug$", msg.topic) != None or
                    re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/prio$", msg.topic) != None):
                self._validate_value(msg, int, [(0, 1)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/chargemode/selected$", msg.topic) != None:
                self._validate_value(msg, str, pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/chargemode/instant_charging/current$", msg.topic) != None:
                self._validate_value(msg, int, [(6, 32)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/chargemode/instant_charging/limit/selected$", msg.topic) != None:
                self._validate_value(msg, str, pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/chargemode/instant_charging/limit/soc$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 100)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/chargemode/instant_charging/limit/amount$", msg.topic) != None:
                self._validate_value(msg, int, [(2, 100)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/chargemode/pv_charging/feed_in_limit$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/chargemode/pv_charging/min_current$", msg.topic) != None:
                self._validate_value(msg, int, [(6, 32)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/chargemode/pv_charging/min_soc$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 100)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/chargemode/pv_charging/min_soc_current$", msg.topic) != None:
                self._validate_value(msg, int, [(6, 32)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/chargemode/pv_charging/max_soc$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 100)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/chargemode/scheduled_charging/[1-9][0-9]*/active$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)], pub_json = True)
            elif (re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/chargemode/scheduled_charging/[1-9][0-9]*/frequency/selected$", msg.topic) != None or
                    re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/chargemode/scheduled_charging/[1-9][0-9]*/frequency/once$", msg.topic) != None):
                self._validate_value(msg, str, pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/chargemode/scheduled_charging/[1-9][0-9]*/frequency/weekly$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)], collection=list, pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/chargemode/scheduled_charging/[1-9][0-9]*/time$", msg.topic) != None:
                self._validate_value(msg, str, pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/chargemode/scheduled_charging/[1-9][0-9]*/soc$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 100)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/time_charging/active$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/time_charging/[1-9][0-9]*/active$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)], pub_json = True)
            elif (re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/time_charging/[1-9][0-9]*/frequency/selected$", msg.topic) != None or
                    re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/time_charging/[1-9][0-9]*/frequency/once$", msg.topic) != None):
                self._validate_value(msg, str, pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/time_charging/[1-9][0-9]*/frequency/weekly$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)], collection=list, pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/time_charging/[1-9][0-9]*/time$", msg.topic) != None:
                self._validate_value(msg, str, collection = list, pub_json = True)
            elif re.search("^openWB/set/vehicle/template/charge_template/[1-9][0-9]*/time_charging/[1-9][0-9]*/current$", msg.topic) != None:
                self._validate_value(msg, int, [(6, 32)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/ev_template/[1-9][0-9]*/name$", msg.topic) != None:
                self._validate_value(msg, str, pub_json = True)
            elif re.search("^openWB/set/vehicle/template/ev_template/[1-9][0-9]*/average_consump$", msg.topic) != None:
                self._validate_value(msg, float, [(0, None)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/ev_template/[1-9][0-9]*/battery_capacity$", msg.topic) != None:
                self._validate_value(msg, int, [(0, None)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/ev_template/[1-9][0-9]*/max_phases$", msg.topic) != None:
                self._validate_value(msg, int, [(1, 3)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/ev_template/[1-9][0-9]*/min_current$", msg.topic) != None:
                self._validate_value(msg, int, [(6, 32)], pub_json = True)
            elif (re.search("^openWB/set/vehicle/template/ev_template/[1-9][0-9]*/max_current_one_phase$", msg.topic) != None or
                    re.search("^openWB/set/vehicle/template/ev_template/[1-9][0-9]*/max_current_multi_phases$", msg.topic) != None):
                self._validate_value(msg, int, [(0, 0), (6, 32)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/ev_template/[1-9][0-9]*/control_pilot_interruption$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)], pub_json = True)
            elif re.search("^openWB/set/vehicle/template/ev_template/[1-9][0-9]*/control_pilot_interruption_duration$", msg.topic) != None:
                self._validate_value(msg, int, [(4, 15)], pub_json = True)
            else:
                log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))
        except Exception as e:
            log.exception_logging(e)

    def process_chargepoint_topic(self, client, userdata, msg):
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
            if (re.search("^openWB/set/chargepoint/get/counter_all$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/get/power_all$", msg.topic) != None):
                self._validate_value(msg, float, [(0, None)])
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/charging_ev$", msg.topic) != None:
                self._validate_value(msg, int, [(-1, None)])
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/current$", msg.topic) != None:
                self._validate_value(msg, float, [(6, 32), (0, 0)])
            elif (re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/energy_to_charge$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/required_power$", msg.topic) != None):
                self._validate_value(msg, int, [(0, None)])
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/phases_to_use$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 3)])
            elif (re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/manual_lock$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/perform_control_pilot_interruption$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/perform_phase_switch$", msg.topic) != None):
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/set/autolock_state$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 4)])
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/template", msg.topic) != None:
                self._validate_value(msg, int, [(0, None)])
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/name", msg.topic) != None:
                self._validate_value(msg, str)
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/max_current", msg.topic) != None:
                self._validate_value(msg, int, [(6, 32)])
            elif (re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/connected_phases", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/phase_1", msg.topic) != None):
                self._validate_value(msg, int, [(0, 3)])
            elif (re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/auto_phase_switch_hw", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/control_pilot_interruption_hw", msg.topic) != None):
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/connection_module/[a-z,_]+/ip_address$", msg.topic) != None:
                self._validate_value(msg, str)
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/connection_module/external_openwb/chargepoint$", msg.topic) != None:
                self._validate_value(msg, int, [(0, None)])
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/connection_module/satellite/id$", msg.topic) != None:
                self._validate_value(msg, int, [(1, 254)])
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/connection_module/[a-z,_]+/timeout$", msg.topic) != None:
                self._validate_value(msg, int, [(0, None)])
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/connection_module/nrg/mac$", msg.topic) != None:
                self._validate_value(msg, str)
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/connection_module/tesla/phases$", msg.topic) != None:
                self._validate_value(msg, int, [(1, 3)])
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/connection_module/dac/register$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 99)])
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/connection_module/modbus_evse/source$", msg.topic) != None:
                self._validate_value(msg, str)
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/connection_module/modbus_evse/id$", msg.topic) != None:
                self._validate_value(msg, int, [(1, 254)])
            elif (re.search("^openWB/set/chargepoint/[1-9][0-9]*/get/voltage$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/get/current$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/get/power_factor$", msg.topic) != None):
                self._validate_value(msg, float, [(0, None)], collection=list)
            elif (re.search("^openWB/set/chargepoint/[1-9][0-9]*/get/daily_counter$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/get/power_all$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/get/counter$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/get/charged_since_plugged_counter$", msg.topic) != None):
                self._validate_value(msg, float, [(0, None)])
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/get/phases_in_use", msg.topic) != None:
                self._validate_value(msg, int, [(0, 3)])
            elif (re.search("^openWB/set/chargepoint/[1-9][0-9]*/get/charge_state$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[1-9][0-9]*/get/plug_state$", msg.topic) != None):
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/get/rfid$", msg.topic) != None:
                self._validate_value(msg, int, [(0, None)])
            elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/get/fault_state$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 2)])
            elif (re.search("^openWB/set/chargepoint/[0-9]+/get/fault_str$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[0-9]+/get/state_str$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[0-9]+/get/plug_time$", msg.topic) != None or
                    re.search("^openWB/set/chargepoint/[0-9]+/get/heartbeat$", msg.topic) != None):
                self._validate_value(msg, str)
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
            elif re.search("^openWB/set/chargepoint/template/[1-9][0-9]*/ev$", msg.topic) != None:
                self._validate_value(msg, int, [(0, None)])
            elif re.search("^openWB/set/chargepoint/template/[1-9][0-9]*/rfid_enabling$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)])
            else:
                log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))
        except Exception as e:
            log.exception_logging(e)

    def process_pv_topic(self, client, userdata, msg):
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
            elif (re.search("^openWB/set/pv/[1-9][0-9]*/config/selected$", msg.topic) != None or
                    re.search("^openWB/set/pv/[1-9][0-9]*/config/openwb/selected$", msg.topic) != None or
                    re.search("^openWB/set/pv/[1-9][0-9]*/config/[a-z,_]+/ip_address[1-9,_]*$", msg.topic) != None or
                    re.search("^openWB/set/pv/[1-9][0-9]*/config/[a-z,_]+/url$", msg.topic) != None or
                    re.search("^openWB/set/pv/[1-9][0-9]*/config/[a-z,_]+/source$", msg.topic) != None):
                self._validate_value(msg, str)
            elif re.search("^openWB/set/pv/[1-9][0-9]*/config/[a-z,_]+/id[1-9,_]*$", msg.topic) != None:
                self._validate_value(msg, int, [(0, None)])
            elif re.search("^openWB/set/pv/[1-9][0-9]*/config/kostal_plenticore/name[1-9,_]*$", msg.topic) != None:
                self._validate_value(msg, str)
            elif (re.search("^openWB/set/pv/[1-9][0-9]*/config/sma/webbox$", msg.topic) != None or
                    re.search("^openWB/set/pv/[1-9][0-9]*/config/solaredge/external_meter$", msg.topic) != None):
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/pv/[1-9][0-9]*/config/solarview/port$", msg.topic) != None:
                self._validate_value(msg, int, [(0, None)])
            elif (re.search("^openWB/set/pv/[1-9][0-9]*/config/http/url_power$", msg.topic) != None or 
                    re.search("^openWB/set/pv/[1-9][0-9]*/config/http/url_energy$", msg.topic) != None or
                    re.search("^openWB/set/pv/[1-9][0-9]*/config/json/power$", msg.topic) != None or
                    re.search("^openWB/set/pv/[1-9][0-9]*/config/json/energy$", msg.topic) != None):
                self._validate_value(msg, str)
            elif re.search("^openWB/set/pv/[1-9][0-9]*/config/vzlogger/line$", msg.topic) != None:
                self._validate_value(msg, int, [(0, None)])
            elif re.search("^openWB/set/pv/[1-9][0-9]*/get/fault_state$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 2)])
            elif re.search("^openWB/set/pv/[1-9][0-9]*/get/fault_str$", msg.topic) != None:
                self._validate_value(msg, str)
            elif (re.search("^openWB/set/pv/[1-9][0-9]*/get/daily_yield$", msg.topic) != None or
                    re.search("^openWB/set/pv/[1-9][0-9]*/get/monthly_yield$", msg.topic) != None or
                    re.search("^openWB/set/pv/[1-9][0-9]*/get/yearly_yield$", msg.topic) != None or
                    re.search("^openWB/set/pv/[1-9][0-9]*/get/energy$", msg.topic) != None):
                self._validate_value(msg, float, [(0, None)])
            elif (re.search("^openWB/set/pv/[1-9][0-9]*/get/counter$", msg.topic) != None or
                    re.search("^openWB/set/pv/[1-9][0-9]*/get/power$", msg.topic) != None):
                self._validate_value(msg, int, [(None, 0)])
            elif re.search("^openWB/set/pv/[1-9][0-9]*/get/actual_power_phase$", msg.topic) != None:
                self._validate_value(msg, float, [(0, None)], collection=list)
            else:
                log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))
        except Exception as e:
            log.exception_logging(e)

    def process_bat_topic(self, client, userdata, msg):
        """ Handler für die Hausspeicher-Topics

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
            if (re.search("^openWB/set/bat/config/configured$", msg.topic) != None or 
                    re.search("^openWB/set/bat/set/switch_on_soc_reached$", msg.topic) != None):
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
            elif (re.search("^openWB/set/bat/[1-9][0-9]*/config/selected$", msg.topic) != None or
                    re.search("^openWB/set/bat/[1-9][0-9]*/config/[a-z,_]+/ip_address[1-9,_]*$", msg.topic) != None or
                    re.search("^openWB/set/bat/[1-9][0-9]*/config/[a-z,_]+/api$", msg.topic) != None or
                    re.search("^openWB/set/bat/[1-9][0-9]*/config/[a-z,_]+/url[a-z,_]*$", msg.topic) != None):
                self._validate_value(msg, str)
            elif re.search("^openWB/set/bat/[1-9][0-9]*/config/openwb/version$", msg.topic) != None:
                self._validate_value(msg, str)
            elif re.search("^openWB/set/bat/[1-9][0-9]*/config/[a-z,_]+/consider_pv$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/bat/[1-9][0-9]*/config/[a-z,_]+/number$", msg.topic) != None:
                self._validate_value(msg, int, [(0, None)])
            elif (re.search("^openWB/set/bat/[1-9][0-9]*/config/tesla/registration$", msg.topic) != None or
                    re.search("^openWB/set/bat/[1-9][0-9]*/config/varta/modbus$", msg.topic) != None):
                self._validate_value(msg, int, [(0, 1)])
            elif (re.search("^openWB/set/bat/[1-9][0-9]*/config/json/power$", msg.topic) != None or 
                    re.search("^openWB/set/bat/[1-9][0-9]*/config/json/soc$", msg.topic) != None or
                    re.search("^openWB/set/bat/[1-9][0-9]*/config/mpm3pm/source$", msg.topic) != None):
                self._validate_value(msg, str)
            elif re.search("^openWB/set/bat/[1-9][0-9]*/config/mpm3pm/id$", msg.topic) != None:
                self._validate_value(msg, int, [(1, 254)])
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
        except Exception as e:
            log.exception_logging(e)

    def process_general_topic(self, client, userdata, msg):
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
            elif re.search("^openWB/set/general/chargemode_config/pv_charging/rundown_power$", msg.topic) != None:
                self._validate_value(msg, int, [(0, None)])
            elif re.search("^openWB/set/general/chargemode_config/[a-z,_]+/phases_to_use$", msg.topic) != None:
                self._validate_value(msg, int, [(1, 1), (3, 3)])
            elif (re.search("^openWB/set/general/grid_protection_configured$", msg.topic) != None or
                    re.search("^openWB/set/general/grid_protection_active$", msg.topic) != None or
                    re.search("^openWB/set/general/mqtt_bridge$", msg.topic) != None):
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/general/notifications/selected$", msg.topic) != None:
                self._validate_value(msg, str)
            elif (re.search("^openWB/set/general/notifications/start_loading$", msg.topic) != None or
                    re.search("^openWB/set/general/notifications/stop_loading$", msg.topic) != None or
                    re.search("^openWB/set/general/notifications/plug$", msg.topic) != None or
                    re.search("^openWB/set/general/notifications/smart_home$", msg.topic) != None):
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/general/price_kwh$", msg.topic) != None:
                self._validate_value(msg, float, [(0, 99.99)])
            elif re.search("^openWB/set/general/range_unit$", msg.topic) != None:
                self._validate_value(msg, str)
            else:
                log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))
        except Exception as e:
            log.exception_logging(e)

    def process_optional_topic(self, client, userdata, msg):
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
            if re.search("^openWB/set/optional/load_sharing/active$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/optional/load_sharing/max_current$", msg.topic) != None:
                self._validate_value(msg, int, [(16, 32)])
            elif re.search("^openWB/set/optional/et/active$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)])
            elif (re.search("^openWB/set/optional/et/provider$", msg.topic) != None or
                    re.search("^openWB/set/optional/et/set/timestamp_updated_prices$", msg.topic) != None):
                self._validate_value(msg, str)
            elif re.search("^openWB/set/optional/et/get/pricedict$", msg.topic) != None:
                self._validate_value(msg, float, collection=dict)
            elif re.search("^openWB/set/optional/et/get/price$", msg.topic) != None:
                self._validate_value(msg, float)
            elif re.search("^openWB/set/optional/et/config/max_price$", msg.topic) != None:
                self._validate_value(msg, float)
            else:
                log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))
        except Exception as e:
            log.exception_logging(e)

    def process_counter_topic(self, client, userdata, msg):
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
            if re.search("^openWB/set/counter/set/loadmanagement$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/counter/set/home_consumption$", msg.topic) != None:
                # Inkonsistenz: Kann auch als Float kommen, soll aber immer als Int gepublished werden.
                payload = json.loads(str(msg.payload.decode("utf-8")))
                msg.payload = json.dumps(int(payload)).encode("utf-8")
                self._validate_value(msg, int, [(0, None)])
            elif re.search("^openWB/set/counter/get/hierarchy$", msg.topic) != None:
                self._validate_value(msg, None)
            elif re.search("^openWB/set/counter/[0-9]+/set/consumption_left$", msg.topic) != None:
                self._validate_value(msg, float)
            elif re.search("^openWB/set/counter/[0-9]+/set/current_left$", msg.topic) != None:
                self._validate_value(msg, float, [(0, None)], collection=list)
            elif (re.search("^openWB/set/counter/[0-9]+/config/selected$", msg.topic) != None or
                    re.search("^openWB/set/counter/[0-9]+/config/openwb/version$", msg.topic) != None):
                self._validate_value(msg, str)
            elif (re.search("^openWB/set/counter/[0-9]+/config/discovergy/id$", msg.topic) != None or
                    re.search("^openWB/set/counter/[0-9]+/config/powerfox/id$", msg.topic) != None or
                    re.search("^openWB/set/counter/[0-9]+/config/victron/id$", msg.topic) != None or
                    re.search("^openWB/set/counter/[0-9]+/config/mpm3pm/id$", msg.topic) != None or
                    re.search("^openWB/set/counter/[0-9]+/config/sdm630/id$", msg.topic) != None):
                self._validate_value(msg, int)
            elif (re.search("^openWB/set/counter/[0-9]+/config/fronius_energy_meter/id$", msg.topic) != None or
                    re.search("^openWB/set/counter/[0-9]+/config/fronius_s0/id$", msg.topic) != None):
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/counter/[0-9]+/config/[a-z,_]+/compability_primo$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/counter/[0-9]+/config/[a-z,_]+/compability_gen24$", msg.topic) != None:
                self._validate_value(msg, str)
            elif re.search("^openWB/set/counter/[0-9]+/config/[a-z,_]+/position$", msg.topic) != None:
                self._validate_value(msg, int, [(0, None)])
            elif re.search("^openWB/set/counter/[0-9]+/config/[a-z,_]+/ip_address$", msg.topic) != None:
                self._validate_value(msg, str)
            elif re.search("^openWB/set/counter/[0-9]+/config/sma_homemanager/serial_number$", msg.topic) != None:
                self._validate_value(msg, int, [(0, None)])
            elif re.search("^openWB/set/counter/[0-9]+/config/[a-z,_]+/url[a-z,1-9,_]*$", msg.topic) != None:
                self._validate_value(msg, str)
            elif re.search("^openWB/set/counter/[0-9]+/config/solarlog/compability$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)])
            elif (re.search("^openWB/set/counter/[0-9]+/config/json/power$", msg.topic) != None or
                    re.search("^openWB/set/counter/[0-9]+/config/json/imported$", msg.topic) != None or
                    re.search("^openWB/set/counter/[0-9]+/config/json/exported$", msg.topic) != None or
                    re.search("^openWB/set/counter/[0-9]+/config/[a-z,_]+/source$", msg.topic) != None or
                    re.search("^openWB/set/counter/[0-9]+/config/vz_logger/line[a-z,_]+$", msg.topic) != None):
                self._validate_value(msg, str)
            elif re.search("^openWB/set/counter/[0-9]+/config/equalisation/active$", msg.topic) != None:
                self._validate_value(msg, int, [(0, 1)])
            elif re.search("^openWB/set/counter/[0-9]+/config/equalisation/time$", msg.topic) != None:
                self._validate_value(msg, int, [(0, None)])
            elif re.search("^openWB/set/counter/[0-9]+/config/max_current$", msg.topic) != None:
                self._validate_value(msg, int, [(7, 1500)], collection=list)
            elif re.search("^openWB/set/counter/[0-9]+/config/max_consumption$", msg.topic) != None:
                self._validate_value(msg, int, [(2000, 1000000)])
            elif re.search("^openWB/set/counter/[0-9]+/get/power_all$", msg.topic) != None:
                self._validate_value(msg, int)
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
        except Exception as e:
            log.exception_logging(e)

    def process_graph_topic(self, client, userdata, msg):
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
            if False:
                pass
            else:
                log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))
        except Exception as e:
            log.exception_logging(e)

    # def processSmarthomeTopic(self, client, userdata, msg):
    #     """
    #     """
    #     pass

