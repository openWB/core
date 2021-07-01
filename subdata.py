""" Modul, um die Daten vom Broker zu erhalten.
"""

import json
import paho.mqtt.client as mqtt
import re

import bat
import chargelog
import chargepoint
import counter
import ev
import general
import graph
import log
import optional
import pub
import pv

class subData():
    """ Klasse, die die benötigten Topics abonniert, die Instanzen ertstellt, wenn z.b. ein Modul neu konfiguriert wird, 
    Instanzen löscht, wenn Module gelöscht werden, und die Werte in die Attribute der Instanzen schreibt.
    """

    #Instanzen
    cp_data={}
    cp_template_data={}
    pv_data={}
    ev_data={}
    ev_template_data={}
    ev_charge_template_data={}
    counter_data={}
    bat_module_data={}
    general_data={}
    optional_data={}

    def __init__(self, event_ev_template, event_charge_template, loadvarsdone):
        self.event_ev_template = event_ev_template
        self.event_charge_template = event_charge_template
        self.loadvarsdone = loadvarsdone
        self.heartbeat = False

    def sub_topics(self):
        """ abonniert alle Topics.
        """
        try:
            mqtt_broker_ip = "localhost"
            client = mqtt.Client("openWB-mqttsub-" + self.getserial())
            # ipallowed='^[0-9.]+$'
            # nameallowed='^[a-zA-Z ]+$'
            # namenumballowed='^[0-9a-zA-Z ]+$'

            client.on_connect = self.on_connect
            client.on_message = self.on_message
            client.message_callback_add("openWB/vehicle/#", self._process_topics)
            client.message_callback_add("openWB/chargepoint/#", self._process_topics)
            client.message_callback_add("openWB/pv/#", self._process_topics)
            client.message_callback_add("openWB/bat/#", self._process_topics)
            client.message_callback_add("openWB/general/#", self._process_topics)
            client.message_callback_add("openWB/optional/#", self._process_topics)
            client.message_callback_add("openWB/counter/#", self._process_topics)
            client.message_callback_add("openWB/log/#", self._process_topics)
            client.message_callback_add("openWB/loadvarsdone", self._process_topics)

            client.connect(mqtt_broker_ip, 1883)
            client.loop_forever()
            client.disconnect()
        except Exception as e:
            log.exception_logging(e)

    def _process_topics(self, client, userdata, msg):
        """
        """
        self.heartbeat = True
        if "openWB/vehicle/" in msg.topic:
            self.process_vehicle_topic(client, userdata, msg)
        elif "openWB/chargepoint/" in msg.topic:
            self.process_chargepoint_topic(client, userdata, msg)
        elif "openWB/pv/" in msg.topic:
            self.process_pv_topic(client, userdata, msg)
        elif "openWB/bat/" in msg.topic:
            self.process_bat_topic(client, userdata, msg)
        elif "openWB/general/" in msg.topic:
            self.process_general_topic(client, userdata, msg)
        elif "openWB//optional/" in msg.topic:
            self.process_optional_topic(client, userdata, msg)
        elif "openWB/counter/" in msg.topic:
            self.process_counter_topic(client, userdata, msg)
        elif "openWB/log/" in msg.topic:
            self.process_log_topic(client, userdata, msg)
        elif "openWB/set/loadvarsdone" in msg.topic:
            self.process_loadvarsdone(client, userdata, msg)

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

    def get_index(self, topic):
        """extrahiert den Index aus einem Topic (Zahl zwischen zwei // oder am Stringende)

         Parameters
        ----------
        topic : str
            Topic, aus dem der Index extrahiert wird
        """
        index=re.search('(?!/)([0-9]*)(?=/|$)', topic)
        return index.group()

    def get_second_index(self, topic):
        """extrahiert den zweiten Index aus einem Topic (Zahl zwischen zwei //)

            Parameters
        ----------
        topic : str
            Topic, aus dem der Index extrahiert wird
        """
        index=re.search('^.+/([0-9]*)/.+/([1-9][0-9]*)/.+$', topic)
        return index.group(2)

    def set_json_payload(self, dict, msg):
        """ dekodiert das JSON-Objekt und setzt diesen für den Value in das übergebene Dictionary, als Key wird der Name nach dem letzten / verwendet.

         Parameters
        ----------
        dict : dictionary
            Dictionary, in dem der Wert abgelegt wird
        msg : 
            enthält den Payload als json-Objekt
        """
        try:
            key=re.search("/([a-z,A-Z,0-9,_]+)(?!.*/)", msg.topic).group(1)
            if msg.payload:
                dict[key]=json.loads(str(msg.payload.decode("utf-8")))
            else:
                if key in dict:
                    dict.pop(key)
        except Exception as e:
            log.exception_logging(e)
 
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
            index=self.get_index(msg.topic)
            if re.search("^openWB/vehicle/[0-9]+/.+$", msg.topic) != None:
                if "ev"+index not in self.ev_data:
                    self.ev_data["ev"+index]=ev.ev(int(index))
                if re.search("^openWB/vehicle/[0-9]+$", msg.topic) != None:
                    if json.loads(str(msg.payload.decode("utf-8")))=="":
                        if "ev"+index in self.ev_data:
                            self.ev_data.pop("ev"+index)
                else:
                    if re.search("^openWB/vehicle/[0-9]+/get.+$", msg.topic) != None:
                        if "get" not in self.ev_data["ev"+index].data:
                            self.ev_data["ev"+index].data["get"]={}
                        self.set_json_payload(self.ev_data["ev"+index].data["get"], msg)
                    elif re.search("^openWB/vehicle/[0-9]+/set.+$", msg.topic) != None:
                        if "set" not in self.ev_data["ev"+index].data:
                            self.ev_data["ev"+index].data["set"]={}
                        self.set_json_payload(self.ev_data["ev"+index].data["set"], msg)
                    elif re.search("^openWB/vehicle/[0-9]+/soc/config/.+$", msg.topic) != None:
                        if "soc" not in self.ev_data["ev"+index].data:
                            self.ev_data["ev"+index].data["soc"]={}
                        if "config" not in self.ev_data["ev"+index].data["soc"]:
                            self.ev_data["ev"+index].data["soc"]["config"]={}
                        self.set_json_payload(self.ev_data["ev"+index].data["soc"]["config"], msg)
                    elif re.search("^openWB/vehicle/[0-9]+/soc/get/.+$", msg.topic) != None:
                        if "soc" not in self.ev_data["ev"+index].data:
                            self.ev_data["ev"+index].data["soc"]={}
                        if "get" not in self.ev_data["ev"+index].data["soc"]:
                            self.ev_data["ev"+index].data["soc"]["get"]={}
                        self.set_json_payload(self.ev_data["ev"+index].data["soc"]["get"], msg)
                    elif re.search("^openWB/vehicle/[0-9]+/match_ev/.+$", msg.topic) != None:
                        if "match_ev" not in self.ev_data["ev"+index].data:
                            self.ev_data["ev"+index].data["match_ev"]={}
                        self.set_json_payload(self.ev_data["ev"+index].data["match_ev"], msg)
                    elif re.search("^openWB/vehicle/[0-9]+/control_parameter/.+$", msg.topic) != None:
                        if "control_parameter" not in self.ev_data["ev"+index].data:
                            self.ev_data["ev"+index].data["control_parameter"]={}
                        self.set_json_payload(self.ev_data["ev"+index].data["control_parameter"], msg)
                    else: 
                        self.set_json_payload(self.ev_data["ev"+index].data, msg)
            elif re.search("^openWB/vehicle/template/charge_template/[0-9]+$", msg.topic) != None:
                if json.loads(str(msg.payload.decode("utf-8")))=="":
                    if "ct"+index in self.ev_charge_template_data:
                        self.ev_charge_template_data.pop("ct"+index)
                else:
                    if "ct"+index not in self.ev_charge_template_data:
                        self.ev_charge_template_data["ct"+index]=ev.chargeTemplate(int(index))
                    self.ev_charge_template_data["ct"+index].data = json.loads(str(msg.payload.decode("utf-8")))
                    self.event_charge_template.set()
            elif re.search("^openWB/vehicle/template/ev_template/[0-9]+$", msg.topic) != None:
                if json.loads(str(msg.payload.decode("utf-8")))=="":
                    if "et"+index in self.ev_template_data:
                        self.ev_template_data.pop("et"+index)
                else:
                    if "et"+index not in self.ev_template_data:
                        self.ev_template_data["et"+index]=ev.evTemplate(int(index))
                    self.ev_template_data["et"+index].data = json.loads(str(msg.payload.decode("utf-8")))
                    self.event_ev_template.set()
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
            if re.search("^openWB/chargepoint/[1-9][0-9]*$", msg.topic) != None:
                index=self.get_index(msg.topic)
                if json.loads(str(msg.payload.decode("utf-8")))=="":
                    if "cp"+index in self.cp_data:
                        self.cp_data.pop("cp"+index)
            elif re.search("^openWB/chargepoint/[1-9][0-9]*/.+$", msg.topic) != None:
                index=self.get_index(msg.topic)
                if "cp"+index not in self.cp_data:
                    self.cp_data["cp"+index]=chargepoint.chargepoint(int(index))
                if re.search("^openWB/chargepoint/[1-9][0-9]*/set/.+$", msg.topic) != None:
                    if "set" not in self.cp_data["cp"+index].data:
                        self.cp_data["cp"+index].data["set"]={}
                    self.set_json_payload(self.cp_data["cp"+index].data["set"], msg)
                elif re.search("^openWB/chargepoint/[1-9][0-9]*/get/.+$", msg.topic) != None:
                    if "get" not in self.cp_data["cp"+index].data:
                        self.cp_data["cp"+index].data["get"]={}
                    self.set_json_payload(self.cp_data["cp"+index].data["get"], msg)
                elif re.search("^openWB/chargepoint/[1-9][0-9]*/config$", msg.topic) != None:
                    self.set_json_payload(self.cp_data["cp"+index].data, msg)
            elif re.search("^openWB/chargepoint/template/[1-9][0-9]*$", msg.topic) != None:
                index=self.get_index(msg.topic)
                if json.loads(str(msg.payload.decode("utf-8")))==1:
                    if "cpt"+index not in self.cp_template_data:
                        self.cp_template_data["cpt"+index]=chargepoint.cpTemplate()
                else:
                    if "cpt"+index in self.cp_template_data:
                        self.cp_template_data.pop("cpt"+index)
            elif re.search("^openWB/chargepoint/template/[1-9][0-9]*/.+$", msg.topic) != None:
                index=self.get_index(msg.topic)
                if "cpt"+index not in self.cp_template_data:
                    self.cp_template_data["cpt"+index]=chargepoint.cpTemplate()
                if re.search("^openWB/chargepoint/template/[1-9][0-9]*/autolock/.+$", msg.topic) != None:
                    if "autolock" not in self.cp_template_data["cpt"+index].data:
                        self.cp_template_data["cpt"+index].data["autolock"]={}
                    if re.search("^openWB/chargepoint/template/[1-9][0-9]*/autolock/[1-9][0-9]*/.+$", msg.topic) != None:
                        index_second=self.get_second_index(msg.topic)
                        if "plan"+index_second not in self.cp_template_data["cpt"+index].data["autolock"]:
                            self.cp_template_data["cpt"+index].data["autolock"]["plan"+index_second]={}
                        if re.search("^openWB/chargepoint/template/[1-9][0-9]*/autolock/[1-9][0-9]*/frequency/.+$", msg.topic) != None:
                            if "frequency" not in self.cp_template_data["cpt"+index].data["autolock"]["plan"+index_second]:
                                self.cp_template_data["cpt"+index].data["autolock"]["plan"+index_second]["frequency"]={}
                            self.set_json_payload(self.cp_template_data["cpt"+index].data["autolock"]["plan"+index_second]["frequency"], msg)
                        else:
                            self.set_json_payload(self.cp_template_data["cpt"+index].data["autolock"]["plan"+index_second], msg)
                    else:
                        self.set_json_payload(self.cp_template_data["cpt"+index].data["autolock"], msg)
                else:
                    self.set_json_payload(self.cp_template_data["cpt"+index].data, msg)
            elif re.search("^openWB/chargepoint/get/.+$", msg.topic) != None:
                if "all" not in self.cp_data:
                    self.cp_data["all"]=chargepoint.allChargepoints()
                self.set_json_payload(self.cp_data["all"].data, msg)
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
            if re.search("^openWB/pv$", msg.topic) != None:
                if json.loads(str(msg.payload.decode("utf-8")))=="":
                    if "all" in self.pv_data:
                        self.pv_data.pop("all")
            elif re.search("^openWB/pv/[1-9][0-9]*/.+$", msg.topic) != None:
                index=self.get_index(msg.topic)
                if "all" not in self.pv_data:
                    self.pv_data["all"] = pv.pv()
                if "pv"+index not in self.pv_data:
                    self.pv_data["pv"+index]=pv.pvModule()
                if re.search("^openWB/pv/[1-9][0-9]*/config/.+$", msg.topic) != None:
                    if "config" not in self.pv_data["pv"+index].data:
                        self.pv_data["pv"+index].data["config"]={}
                    self.set_json_payload(self.pv_data["pv"+index].data["config"], msg)
                elif re.search("^openWB/pv/[1-9][0-9]*/get/.+$", msg.topic) != None:
                    if "get" not in self.pv_data["pv"+index].data:
                        self.pv_data["pv"+index].data["get"]={}
                    self.set_json_payload(self.pv_data["pv"+index].data["get"], msg)
            elif re.search("^openWB/pv/.+$", msg.topic) != None:
                if "all" not in self.pv_data:
                    self.pv_data["all"]=pv.pv()
                if re.search("^openWB/pv/config/.+$", msg.topic) != None:
                    if "config" not in self.pv_data["all"].data:
                        self.pv_data["all"].data["config"]={}
                    self.set_json_payload(self.pv_data["all"].data["config"], msg)
                elif re.search("^openWB/pv/get/.+$", msg.topic) != None:
                    if "get" not in self.pv_data["all"].data:
                        self.pv_data["all"].data["get"]={}
                    self.set_json_payload(self.pv_data["all"].data["get"], msg)
                elif re.search("^openWB/pv/set/.+$", msg.topic) != None:
                    if "set" not in self.pv_data["all"].data:
                        self.pv_data["all"].data["set"]={}
                    self.set_json_payload(self.pv_data["all"].data["set"], msg)
        except Exception as e:
            log.exception_logging(e)

    def process_bat_topic(self, client, userdata, msg):
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
            if re.search("^openWB/bat$", msg.topic) != None:
                if json.loads(str(msg.payload.decode("utf-8")))=="":
                    if "all" in self.bat_module_data:
                        self.bat_module_data.pop("all")
            elif re.search("^openWB/bat/[1-9][0-9]*/.+$", msg.topic) != None:
                index=self.get_index(msg.topic)
                if "all" not in self.bat_module_data:
                    self.bat_module_data["all"] = bat.bat()
                if "bat"+index not in self.bat_module_data:
                    self.bat_module_data["bat"+index]=bat.batModule()
                if re.search("^openWB/bat/[1-9][0-9]*/config$", msg.topic) != None:
                    self.set_json_payload(self.bat_module_data["bat"+index].data, msg)
                elif re.search("^openWB/bat/[1-9][0-9]*/get/.+$", msg.topic) != None:
                    if "get" not in self.bat_module_data["bat"+index].data:
                        self.bat_module_data["bat"+index].data["get"]={}
                    self.set_json_payload(self.bat_module_data["bat"+index].data["get"], msg)
                elif re.search("^openWB/bat/[1-9][0-9]*/set/.+$", msg.topic) != None:
                    if "set" not in self.bat_module_data["bat"+index].data:
                        self.bat_module_data["bat"+index].data["set"]={}
                    self.set_json_payload(self.bat_module_data["bat"+index].data["set"], msg)
            elif re.search("^openWB/bat/.+$", msg.topic) != None:
                if "all" not in self.bat_module_data:
                    self.bat_module_data["all"]=bat.bat()
                if re.search("^openWB/bat/get/.+$", msg.topic) != None:
                    if "get" not in self.bat_module_data["all"].data:
                        self.bat_module_data["all"].data["get"] = {}
                    self.set_json_payload(self.bat_module_data["all"].data["get"], msg)
                elif re.search("^openWB/bat/set/.+$", msg.topic) != None:
                    if "set" not in self.bat_module_data["all"].data:
                        self.bat_module_data["all"].data["set"] = {}
                    self.set_json_payload(self.bat_module_data["all"].data["set"], msg)
                elif re.search("^openWB/bat/config/.+$", msg.topic) != None:
                    if "config" not in self.bat_module_data["all"].data:
                        self.bat_module_data["all"].data["config"] = {}
                    self.set_json_payload(self.bat_module_data["all"].data["config"], msg)
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
            if re.search("^openWB/general/.+$", msg.topic) != None:
                if "general" not in self.general_data:
                    self.general_data["general"]=general.general()
                if re.search("^openWB/general/notifications/.+$", msg.topic) != None:
                    if "notifications" not in self.general_data["general"].data:
                        self.general_data["general"].data["notifications"]={}
                    self.set_json_payload(self.general_data["general"].data["notifications"], msg)
                elif re.search("^openWB/general/chargemode_config/.+$", msg.topic) != None:
                    if "chargemode_config" not in self.general_data["general"].data:
                        self.general_data["general"].data["chargemode_config"]={}
                    if re.search("^openWB/general/chargemode_config/pv_charging/.+$", msg.topic) != None:
                        if "pv_charging" not in self.general_data["general"].data["chargemode_config"]:
                            self.general_data["general"].data["chargemode_config"]["pv_charging"]={}
                        self.set_json_payload(self.general_data["general"].data["chargemode_config"]["pv_charging"], msg)
                    elif re.search("^openWB/general/chargemode_config/instant_charging/.+$", msg.topic) != None:
                        if "instant_charging" not in self.general_data["general"].data["chargemode_config"]:
                            self.general_data["general"].data["chargemode_config"]["instant_charging"]={}
                        self.set_json_payload(self.general_data["general"].data["chargemode_config"]["instant_charging"], msg)
                    elif re.search("^openWB/general/chargemode_config/scheduled_charging/.+$", msg.topic) != None:
                        if "scheduled_charging" not in self.general_data["general"].data["chargemode_config"]:
                            self.general_data["general"].data["chargemode_config"]["scheduled_charging"]={}
                        self.set_json_payload(self.general_data["general"].data["chargemode_config"]["scheduled_charging"], msg)
                    elif re.search("^openWB/general/chargemode_config/time_charging/.+$", msg.topic) != None:
                        if "time_charging" not in self.general_data["general"].data["chargemode_config"]:
                            self.general_data["general"].data["chargemode_config"]["time_charging"]={}
                        self.set_json_payload(self.general_data["general"].data["chargemode_config"]["time_charging"], msg)
                    elif re.search("^openWB/general/chargemode_config/standby/.+$", msg.topic) != None:
                        if "standby" not in self.general_data["general"].data["chargemode_config"]:
                            self.general_data["general"].data["chargemode_config"]["standby"]={}
                        self.set_json_payload(self.general_data["general"].data["chargemode_config"]["standby"], msg)
                    else:
                        self.set_json_payload(self.general_data["general"].data["chargemode_config"], msg)
                else: 
                    self.set_json_payload(self.general_data["general"].data, msg)
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
            if re.search("^openWB/optional/.+$", msg.topic) != None:
                if "optional" not in self.optional_data:
                    self.optional_data["optional"]=optional.optional()
                if re.search("^openWB/optional/led/.+$", msg.topic) != None:
                    if "led" not in self.optional_data["optional"].data:
                        self.optional_data["optional"].data["led"]={}
                    self.set_json_payload(self.optional_data["optional"].data["led"], msg)
                elif re.search("^openWB/optional/rfid/.+$", msg.topic) != None:
                    if "rfid" not in self.optional_data["optional"].data:
                        self.optional_data["optional"].data["rfid"]={}
                    self.set_json_payload(self.optional_data["optional"].data["rfid"], msg)
                elif re.search("^openWB/optional/int_display/.+$", msg.topic) != None:
                    if "int_display" not in self.optional_data["optional"].data:
                        self.optional_data["optional"].data["int_display"]={}
                    self.set_json_payload(self.optional_data["optional"].data["int_display"], msg)
                elif re.search("^openWB/optional/et/.+$", msg.topic) != None:
                    if "et" not in self.optional_data["optional"].data:
                        self.optional_data["optional"].data["et"]={}
                    if re.search("^openWB/optional/et/get/.+$", msg.topic) != None:
                        if "get" not in self.optional_data["optional"].data["et"]:
                            self.optional_data["optional"].data["et"]["get"]={}
                        self.set_json_payload(self.optional_data["optional"].data["et"]["get"], msg)
                    elif re.search("^openWB/optional/et/config/.+$", msg.topic) != None:
                        if "config" not in self.optional_data["optional"].data["et"]:
                            self.optional_data["optional"].data["et"]["config"]={}
                        self.set_json_payload(self.optional_data["optional"].data["et"]["config"], msg)
                    else:
                        self.set_json_payload(self.optional_data["optional"].data["et"], msg)
                else: 
                    self.set_json_payload(self.optional_data["optional"].data, msg)
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
            if re.search("^openWB/counter/[0-9]+$", msg.topic) != None:
                index=self.get_index(msg.topic)
                if json.loads(str(msg.payload.decode("utf-8")))=="":
                    if "counter"+index in self.counter_data:
                        self.counter_data.pop("counter"+index)
            elif re.search("^openWB/counter/[0-9]+/.+$", msg.topic) != None:
                index=self.get_index(msg.topic)
                if "counter"+index not in self.counter_data:
                    self.counter_data["counter"+index]=counter.counter()
                if re.search("^openWB/counter/[0-9]+/get.+$", msg.topic) != None:
                    if "get" not in self.counter_data["counter"+index].data:
                        self.counter_data["counter"+index].data["get"]={}
                    self.set_json_payload(self.counter_data["counter"+index].data["get"], msg)
                elif re.search("^openWB/counter/[0-9]+/config$", msg.topic) != None:
                    self.set_json_payload(self.counter_data["counter"+index].data, msg)
            elif re.search("^openWB/counter/.+$", msg.topic) != None:
                if "all" not in self.counter_data:
                    self.counter_data["all"]=counter.counterAll()
                if re.search("^openWB/counter/get.+$", msg.topic) != None:
                    if "get" not in self.counter_data["all"].data:
                        self.counter_data["all"].data["get"]={}
                    self.set_json_payload(self.counter_data["all"].data["get"], msg)
                elif re.search("^openWB/counter/set.+$", msg.topic) != None:
                    if "set" not in self.counter_data["all"].data:
                        self.counter_data["all"].data["set"]={}
                    self.set_json_payload(self.counter_data["all"].data["set"], msg)
        except Exception as e:
            log.exception_logging(e)

    def process_log_topic(self, client, userdata, msg):
        """Handler für die Log-Topics

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
            if "openWB/log/request" in msg.topic:
                chargelog.get_log_data(json.loads(str(msg.payload.decode("utf-8"))))
        except Exception as e:
            log.exception_logging(e)

    def process_loadvarsdone(self, client, userdata, msg):
        try:
            if json.loads(str(msg.payload.decode("utf-8"))) == 1:
                self.loadvarsdone.set()
                pub.pub("openWB/loadvarsdone", 0)
            else:
                self.loadvarsdone.clear()
        except Exception as e:
            log.exception_logging(e)