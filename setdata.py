""" Modul, um die Daten vom Broker zu erhalten.
"""

import json
import paho.mqtt.client as mqtt
import re

import log
import pub

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
        client.message_callback_add("openWB/set/graph/#", self.process_graph_topic)
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
        client.subscribe("openWB/#", 2)

    def on_message(self, client, userdata, msg):
        """ wartet auf eingehende Topics.
        """
        #self.log_mqtt()
        #print("Unknown topic: "+msg.topic+", "+str(msg.payload.decode("utf-8")))

    def _validate_value(self, msg, data_type, min_value = None, max_value = None):
        """ prüft, ob der Wert vom angegebenen Typ ist.

        Parameter
        ---------
        msg:
            Broker-Nachricht
        data_type: float, int
            Datentyp
        min_value: int/float
            Minimalwert
        max_value= int/float
            Maximalwert
        """
        value = json.loads(str(msg.payload.decode("utf-8")))
        if data_type == str:
            if isinstance(value, str) == False:
                log.message_debug_log("error", "Payload ungueltig: Topic "+str(msg.topic)+", Payload "+str(value)+" sollte ein String sein.")
                return
        elif self._validate_min_max_value(value, msg, data_type, min_value, max_value) == False:
             return 
        pub.pub(msg.topic.replace('set/', '', 1), value)

    def _validate_list_value(self, msg, data_type, min_value = None, max_value = None):
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
        """
        value = json.loads(str(msg.payload.decode("utf-8")))
        if isinstance(value, list) == True:
            for item in value:
                if self._validate_min_max_value(item, msg, data_type, min_value, max_value) == False:
                    break
            else:
                pub.pub(msg.topic.replace('set/', '', 1), value)
        else:
            log.message_debug_log("error", "Payload ungueltig: Topic "+str(msg.topic)+", Payload "+str(value)+" sollte eine Liste sein.")

    def _validate_min_max_value(self, value, msg, data_type, min_value = None, max_value = None):
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
        if isinstance(value, data_type) == True:
            if min_value != None:
                if value <= min_value:
                    log.message_debug_log("error", "Payload ungültig: Topic "+str(msg.topic)+", Payload "+str(value)+" kleiner als Minimalwert.")
                    return False
            if max_value != None:
                if value >= max_value:
                    log.message_debug_log("error", "Payload ungueltig: Topic "+str(msg.topic)+", Payload "+str(value)+" groesser als Maxmalwert.")
                    return False
            return True
        else:
            if data_type == int:
                log.message_debug_log("error", "Payload ungueltig: Topic "+str(msg.topic)+", Payload "+str(value)+" sollte ein Int sein.")
            elif data_type == float:
                log.message_debug_log("error", "Payload ungueltig: Topic "+str(msg.topic)+", Payload "+str(value)+" sollte ein Float sein.")
            return False
        
 
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
        if False:
            pass
        else:
            log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))

    def subprocess_vehicle_chargemode_topic(self, msg):
        """ Handler für die EV-Chargemode-Template-Topics

         Parameters
        ----------
        msg:
            enthält Topic und Payload
        """
        if False:
            pass
        else:
            log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))

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
        if re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/connection_module/[a-z,_]+/ip_address$", msg.topic) != None:
            self._validate_value(msg, str)
        elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/connection_module/external_openwb/chargepoint$", msg.topic) != None:
            self._validate_value(msg, int, min_value=1, max_value=2)
        elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/connection_module/satellite/id$", msg.topic) != None:
            self._validate_value(msg, int, min_value=1, max_value=254)
        elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/connection_module/[a-z,_]+/timeout$", msg.topic) != None:
            self._validate_value(msg, int, min_value=0)
        elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/connection_module/nrg/mac$", msg.topic) != None:
            self._validate_value(msg, str)
        elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/connection_module/tesla/phases$", msg.topic) != None:
            self._validate_value(msg, int, min_value=1, max_value=3)
        elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/connection_module/dac/register$", msg.topic) != None:
            self._validate_value(msg, int, min_value=0, max_value=99)
        elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/connection_module/modbus_evse/source$", msg.topic) != None:
            self._validate_value(msg, str)
        elif re.search("^openWB/set/chargepoint/[1-9][0-9]*/config/connection_module/modbus_evse/id$", msg.topic) != None:
            self._validate_value(msg, int, min_value=1, max_value=254)
        else:
            log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))

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
        if False:
            pass
        else:
            log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))

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
        if re.search("^openWB/set/bat/get/soc$", msg.topic) != None:
            self._validate_value(msg, int, min_value=0, max_value=100)
        elif re.search("^openWB/set/bat/get/power$", msg.topic) != None:
            self._validate_value(msg, int, min_value=0)
        else:
            log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))

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
        if False:
            pass
        else:
            log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))

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
        if False:
            pass
        else:
            log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))

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
        if re.search("^openWB/set/counter/[0-9]*/get/power_all$", msg.topic) != None:
            self._validate_value(msg, int)
        elif (re.search("^openWB/set/counter/[0-9]*/get/current$", msg.topic) != None or
                re.search("^openWB/set/counter/[0-9]*/get/voltage$", msg.topic) != None or
                re.search("^openWB/set/counter/[0-9]*/get/power_phase$", msg.topic) != None or
                re.search("^openWB/set/counter/[0-9]*/get/power_factor$", msg.topic) != None):
            self._validate_list_value(msg, float, min_value=0)
        elif (re.search("^openWB/set/counter/[0-9]*/get/power_average$", msg.topic) != None
                or re.search("^openWB/set/counter/[0-9]*/get/unbalanced_load$", msg.topic) != None
                or re.search("^openWB/set/counter/[0-9]*/get/frequency$", msg.topic) != None
                or re.search("^openWB/set/counter/[0-9]*/get/daily_yield_export$", msg.topic) != None
                or re.search("^openWB/set/counter/[0-9]*/get/daily_yield_import$", msg.topic) != None
                or re.search("^openWB/set/counter/[0-9]*/get/imported$", msg.topic) != None
                or re.search("^openWB/set/counter/[0-9]*/get/exported$", msg.topic) != None):
            self._validate_value(msg, float, min_value=0)
        elif re.search("^openWB/set/counter/[0-9]/get/fault_state$", msg.topic) != None:
            self._validate_value(msg, int, min_value=0, max_value=2)
        elif re.search("^openWB/set/counter/[0-9]/get/fault_str$", msg.topic) != None:
            self._validate_value(msg, str)
        else:
            log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))

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
        if False:
            pass
        else:
            log.message_debug_log("error", "Unbekanntes set-Topic: "+str(msg.topic)+", "+ str(json.loads(str(msg.payload.decode("utf-8")))))

    # def processSmarthomeTopic(self, client, userdata, msg):
    #     """
    #     """
    #     pass

