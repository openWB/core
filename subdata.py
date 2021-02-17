""" Modul, um die Daten vom Broker zu erhalten.
"""

import paho.mqtt.client as mqtt
import re
import threading

import chargepoint
import ev
import prepare
import stats

class subData():
    """ Klasse, die die benötigten Topics abonniert, die Instanzen ertstellt, wenn z.b. ein Modul neu konfiguriert wird, 
    Instanzen löscht, wenn Module gelöscht werden, und die Werte in die Attribute der Instanzen schreibt.
    """

    #Instanzen
    cp_data={}
    cp_template_data={}
    pv_data={}
    pv_module_data={}
    ev_data={}
    ev_template_data={}
    ev_charge_template_data={}
    meter_data={}
    meter_module_data={}
    bat_data={}
    bat_module_data={}
    evu_data={}
    evu_module_data={}

    def __init__(self):
        self.ticker_prepare = threading.Event()
        self.prep=prepare.prepare()

    def sub_topics(self):
        """ abonniert alle Topics.
        """
        mqtt_broker_ip = "localhost"
        client = mqtt.Client("openWB-mqttsub-" + self.getserial())
        ipallowed='^[0-9.]+$'
        nameallowed='^[a-zA-Z ]+$'
        namenumballowed='^[0-9a-zA-Z ]+$'

        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.message_callback_add("openWB/vehicle/#", self.process_vehicle_topic)
        # client.message_callback_add("openWB/chargepoint/#", self.processChargepointTopic)
        # client.message_callback_add("openWB/pv/#", self.processPvTopic)
        # client.message_callback_add("openWB/bat/#", self.processBatTopic)
        # client.message_callback_add("openWB/general/#", self.processGeneralTopic)
        # client.message_callback_add("openWB/optional/#", self.processOptionalTopic)
        # client.message_callback_add("openWB/counter/#", self.processCounterTopic)
        # client.message_callback_add("openWB/graph/#", self.processGraphTopic)
        # client.message_callback_add("openWB/smarthome/#", self.processSmarthomeTopic)
        client.message_callback_add("openWB/lp/#", self.processTest)

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

    def get_index(self, topic):
        """extrahiert den Index aus einemTtopic (zwischen zwei //)
        """
        index=re.search('(?!\/)([0-9]+)(?=\/)', topic)
        return index.group()

    def processTest(self, client, userdata, msg):
        if re.search("^openWB/lp/1/.+$", msg.topic) != None:
            index=self.get_index(msg.topic)
            if "lp"+index not in self.cp_data:
                self.cp_data["lp"+index]=chargepoint.chargepoint()
            if (re.search("^.+/VPhase1$", msg.topic) or re.search("^.+/VPhase2$", msg.topic)) != None:
                self.set_float_payload(self.cp_data["lp"+index].data, msg)
                print(self.cp_data)
                print(self.cp_data["lp1"].data)

    def set_float_payload(self, dict, msg):
        """ setzt den Payload als Float für den Value in das übergebene Dictionary, als Key wird der Name nach dem letzten / verwendet.
        """
        key=re.search("/([a-z,A-Z,0-9]+)(?!.*/)", msg.topic).group(1)
        dict[key]=float(msg.payload)

    def set_int_payload(self, dict, msg):
        """ setzt den Payload als Float für den Value in das übergebene Dictionary, als Key wird der Name nach dem letzten / verwendet.
        """
        key=re.search("/([a-z,A-Z,0-9]+)(?!.*/)", msg.topic).group(1)
        dict[key]=int(msg.payload)

    def set_str_payload(self, dict, msg):
        """ setzt den Payload als Str für den Value in das übergebene Dictionary, als Key wird der Name nach dem letzten / verwendet.
        """
        key=re.search("/([a-z,A-Z,0-9]+)(?!.*/)", msg.topic).group(1)
        print("key"+key)
        dict[key]=str(msg.payload.decode("utf-8"))

    def set_strsplit_payload(self, dict, msg):
        """ setzt den Payload als Liste (String wird an den Kommas getrennt) für den Value in das übergebene Dictionary, als Key wird der Name nach dem letzten / verwendet.
        """
        key=re.search("/([a-z,A-Z,0-9]+)(?!.*/)", msg.topic).group(1)
        print("key"+key)
        dict[key]=str(msg.payload.decode("utf-8")).split(",")
 
    def process_vehicle_topic(self, client, userdata, msg):
        """
        """
        if re.search("^openWB/vehicle/[0-9]+/.+$", msg.topic) != None:
            index=self.get_index(msg.topic)
            if re.search("^openWB/vehicle/[0-9]+$", msg.topic) != None:
                if int(msg.payload)==1:
                    if "ev"+index not in self.ev_data:
                        self.ev_data["ev"+index]=ev.ev()
                else:
                    if "ev"+index in self.ev_data:
                        self.ev_data.pop("ev"+index)
            elif (re.search("^.+/match_ev$", msg.topic) 
            or re.search("^.+/charge_template$", msg.topic) 
            or re.search("^.+/ev_template$", msg.topic)) != None:
                self.set_str_payload(self.ev_data["ev"+index].data, msg)
            elif (re.search("^.+/tag_id$", msg.topic) 
            or re.search("^.+/inactive$", msg.topic)
            or re.search("^.+/request_interval_charging$", msg.topic) 
            or re.search("^.+/reques_interval_not_charging$", msg.topic) 
            or re.search("^.+/request_only_plugged$", msg.topic)) != None:
                self.set_int_payload(self.ev_data["ev"+index].data, msg)
            elif re.search("^openWB/vehicle/[0-9]+/get.+$", msg.topic) != None:
                if "get" not in self.ev_data["ev"+index].data:
                    self.ev_data["ev"+index].data["get"]={}
                if (re.search("^.+/daily_charge_kwh$", msg.topic) 
                or re.search("^.+/km_charged$", msg.topic)
                or re.search("^.+/counter_kwh$", msg.topic) 
                or re.search("^.+/charged_since_plugged_kwh$", msg.topic) ) != None:
                            self.set_float_payload(self.ev_data["ev"+index].data["get"], msg)
        elif "openWB/vehicle/template/chargeTemplate" in msg.topic:
            index=self.get_index(msg.topic)
            if re.search("^openWB/vehicle/template/chargeTemplate/[0-9]+$", msg.topic) != None:
                if int(msg.payload)==1:
                    if "ct"+index not in self.ev_data:
                        self.ev_charge_template_data["ct"+index]=ev.chargeTemplate()
                else:
                    if "ct"+index in self.ev_charge_template_data:
                        self.ev_charge_template_data.pop("ct"+index)
            elif (re.search("^.+/name$", msg.topic) 
            or re.search("^.+/chargemode$", msg.topic)) != None:
                self.set_str_payload(self.ev_charge_template_data["ct"+index].data, msg)
            if (re.search("^.+/load_default$", msg.topic) 
            or re.search("^.+/disable_after_unplug$", msg.topic) 
            or re.search("^.+/prio$", msg.topic)) != None:
                self.set_int_payload(self.ev_charge_template_data["ct"+index].data, msg)
            elif re.search("^openWB/vehicle/template/chargeTemplate/[1-9]+/chargeMode/instantLoad/.+$", msg.topic) != None:
                if "instant_load" not in self.ev_charge_template_data["ct"+index].data:
                    self.ev_charge_template_data["ct"+index].data["instant_load"]={}
                    if re.search("^.+/limit$", msg.topic) != None:
                        self.set_str_payload(self.ev_charge_template_data["ct"+index].data["instant_load"], msg)
                    elif re.search("^.+/soc$", msg.topic) != None:
                        self.set_int_payload(self.ev_charge_template_data["ct"+index].data["instant_load"], msg)
                    elif (re.search("^.+/current$", msg.topic) 
                    or re.search("^.+/amount$", msg.topic)) != None:
                        self.set_float_payload(self.ev_charge_template_data["ct"+index].data["instant_load"], msg)
            elif re.search("^openWB/vehicle/template/chargeTemplate/[1-9]+/chargeMode/pvLoad/.+$", msg.topic) != None:
                if "pv_load" not in self.ev_charge_template_data["ct"+index].data:
                    self.ev_charge_template_data["ct"+index].data["pv_load"]={}
                if (re.search("^.+/bat_prio$", msg.topic) 
                or re.search("^.+/feed_in_limit$", msg.topic) 
                or re.search("^.+/min_current$", msg.topic) 
                or re.search("^.+/min_soc$", msg.topic) 
                or re.search("^.+/min_soc_current$", msg.topic) 
                or re.search("^.+/max_soc$", msg.topic)) != None:
                    self.set_int_payload(self.ev_charge_template_data["ct"+index].data["pv_load"], msg)
            elif re.search("^openWB/vehicle/template/chargeTemplate/[1-9]+/chargeMode/scheduledLoad/.+$", msg.topic) != None:
                if "pv_load" not in self.ev_charge_template_data["ct"+index].data:
                    self.ev_charge_template_data["ct"+index].data["scheduled_load"]={}
                index_second=re.search(".+/([0-9]+)/.+/([0-9]+)/.+", msg.topic).group(2)
                if "plan"+index_second not in self.ev_charge_template_data["ct"+index].data["scheduled_load"]:
                    self.ev_charge_template_data["ct"+index].data["scheduled_load"]["plan"+index_second]={}
                if (re.search("^.+/frequency$", msg.topic) 
                or re.search("^.+/time$", msg.topic)) != None:
                    self.set_str_payload(self.ev_charge_template_data["ct"+index].data["scheduled_load"]["plan"+index_second], msg)
                elif (re.search("^.+/once$", msg.topic) 
                or re.search("^.+/weekly$", msg.topic)) != None:
                    self.set_strsplit_payload(self.ev_charge_template_data["ct"+index].data["scheduled_load"]["plan"+index_second], msg)
                elif re.search("^.+/soc$", msg.topic) != None:
                    self.set_int_payload(self.ev_charge_template_data["ct"+index].data["scheduled_load"]["plan"+index_second], msg)
            elif re.search("^openWB/vehicle/template/chargeTemplate/[1-9]+/time_load$", msg.topic) != None:
                self.set_int_payload(self.ev_charge_template_data["ct"+index].data, msg)
            elif re.search("^openWB/vehicle/template/chargeTemplate/[1-9]+/timeLoad/.+$", msg.topic) != None:
                if "pv_load" not in self.ev_charge_template_data["ct"+index].data:
                    self.ev_charge_template_data["ct"+index].data["time_load"]={}
                index_second=re.search(".+/([0-9]+)/.+/([0-9]+)/.+", msg.topic).group(2)
                if "plan"+index_second not in self.ev_charge_template_data["ct"+index].data["time_load"]:
                    self.ev_charge_template_data["ct"+index].data["time_load"]["plan"+index_second]={}
                if (re.search("^.+/frequency$", msg.topic) 
                or re.search("^.+/time$", msg.topic)) != None:
                    self.set_str_payload(self.ev_charge_template_data["ct"+index].data["time_load"]["plan"+index_second], msg)
                elif (re.search("^.+/once$", msg.topic) 
                or re.search("^.+/weekly$", msg.topic)) != None:
                    self.set_strsplit_payload(self.ev_charge_template_data["ct"+index].data["time_load"]["plan"+index_second], msg)
                elif re.search("^.+/soc$", msg.topic) != None:
                    self.set_int_payload(self.ev_charge_template_data["ct"+index].data["time_load"]["plan"+index_second], msg)
        elif "openWB/vehicle/template/evTemplate" in msg.topic:
            index=self.get_index(msg.topic)
            if re.search("^openWB/vehicle/template/evTemplate/[0-9]+$", msg.topic) != None:
                if int(msg.payload)==1:
                    if "et"+index not in self.ev_template_data:
                        self.ev_template_data["et"+index]=ev.evTemplate()
                else:
                    if "et"+index in self.ev_template_data:
                        self.ev_template_data.pop("et"+index)
            elif re.search("^.+/name$", msg.topic) != None:
                self.set_str_payload(self.ev_template_data["et"+index].data, msg)
            elif (re.search("^.+/average_consump$", msg.topic) 
            or re.search("^.+/battery_capcity$", msg.topic) 
            or re.search("^.+/max_phases$", msg.topic) 
            or re.search("^.+/min_current$", msg.topic) 
            or re.search("^.+/max_current$", msg.topic) 
            or re.search("^.+/control_pilot_interruption$", msg.topic)) != None:
                self.set_int_payload(self.ev_template_data["et"+index].data, msg)

    # def processChargepointTopic(self, topic, payload):
    #     """
    #     """
    #     pass

    # def processPvTopic(self, topic, payload):
    #     """
    #     """
    #     pass

    # def processBatTopic(self, topic, payload):
    #     """
    #     """
    #     pass

    # def processGeneralTopic(self, topic, payload):
    #     """
    #     """
    #     pass

    # def processOptionalTopic(self, topic, payload):
    #     """
    #     """
    #     pass

    # def processCounterTopic(self, topic, payload):
    #     """
    #     """
    #     pass

    # def processGraphTopic(self, topic, payload):
    #     """
    #     """
    #     pass

    # def processSmarthomeTopic(self, topic, payload):
    #     """
    #     """
    #     pass

    #     #keine Reihenfolge imner gucken, ob es Instanz schon gibt
            
            # self.ticker_prepare.clear()
            # seconds = mqttpayload
            # self.ticker_prepare.set()
            # while not self.ticker_prepare.wait(seconds):
            #     self.prep.setup_algorithm() 