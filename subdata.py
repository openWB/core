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
        client.message_callback_add("openWB/vehicle/#", self.processVehicleTopic)
        # client.message_callback_add("openWB/chargepoint/#", self.processChargepointTopic)
        # client.message_callback_add("openWB/pv/#", self.processPvTopic)
        # client.message_callback_add("openWB/bat/#", self.processBatTopic)
        # client.message_callback_add("openWB/general/#", self.processGeneralTopic)
        # client.message_callback_add("openWB/optional/#", self.processOptionalTopic)
        # client.message_callback_add("openWB/counter/#", self.processCounterTopic)
        # client.message_callback_add("openWB/graph/#", self.processGraphTopic)
        # client.message_callback_add("openWB/smarthome/#", self.processSmarthomeTopic)
        #client.message_callback_add("openWB/lp/#", self.processTest)

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
        if msg.topic=="openWB/lp/1/boolChargePointConfigured":
            if "lp1" not in self.cp_data:
                self.cp_data["lp1"]=chargepoint.chargepoint()
            self.cp_data["lp1"].data["boolChargePointConfigured"]=int(msg.payload)
            print(self.cp_data)
            print(self.cp_data["lp1"].data)
 
    def processVehicleTopic(self, client, userdata, msg):
        """
        """
        if "openWB/vehicle/default" in msg.topic:
            if "default" not in self.ev_data:
                self.ev_data["default"]=ev.ev()
            if "matchEV" in msg.topic:
                self.ev_data["default"].data["match_ev"]=str(msg.payload.decode("utf-8"))
            elif "chargetemplate" in msg.topic:
                self.ev_data["default"].data["charge_template"]=str(msg.payload.decode("utf-8"))
            elif "evTemplate" in msg.topic:
                self.ev_data["default"].data["ev_template"]=str(msg.payload.decode("utf-8"))
        elif "openWB/vehicle/template/chargeTemplate" in msg.topic:
            index=self.get_index(msg.topic)
            if "ct"+index not in self.ev_charge_template_data:
                self.ev_charge_template_data["ct"+index] = ev.chargeTemplate()
            if re.search("^openWB/vehicle/template/chargeTemplate/[1-9]+/name$", msg.topic) != None:
                self.ev_charge_template_data["ct"+index].data["name"]=str(msg.payload.decode("utf-8"))
            elif re.search("^openWB/vehicle/template/chargeTemplate/[1-9]+/loadDefault$", msg.topic) != None:
                self.ev_charge_template_data["ct"+index].data["load_default"]=int(msg.payload)
            elif re.search("^openWB/vehicle/template/chargeTemplate/[1-9]+/disableAfterUnplug$", msg.topic) != None:
                self.ev_charge_template_data["ct"+index].data["disable_after_unplug"]=int(msg.payload)
            elif re.search("^openWB/vehicle/template/chargeTemplate/[1-9]+/prio$", msg.topic) != None:
                self.ev_charge_template_data["ct"+index].data["prio"]=int(msg.payload)
            elif re.search("^openWB/vehicle/template/chargeTemplate/[1-9]+/chargeMode$", msg.topic) != None:
                self.ev_charge_template_data["ct"+index].data["chargemode"]=str(msg.payload.decode("utf-8"))
            elif re.search("^openWB/vehicle/template/chargeTemplate/[1-9]+/chargeMode/instantLoad/.+$", msg.topic) != None:
                if "instant_load" not in self.ev_charge_template_data["ct"+index].data:
                    self.ev_charge_template_data["ct"+index].data["instant_load"]={}
                    if "current" in msg.topic:
                        self.ev_charge_template_data["ct"+index].data["instant_load"]["current"]=int(msg.payload)
                    elif "limit" in msg.topic:
                        self.ev_charge_template_data["ct"+index].data["instant_load"]["limit"]=str(msg.payload.decode("utf-8"))
                    elif "soc" in msg.topic:
                        self.ev_charge_template_data["ct"+index].data["instant_load"]["soc"]=int(msg.payload)
                    elif "amount" in msg.topic:
                        self.ev_charge_template_data["ct"+index].data["instant_load"]["amount"]=int(msg.payload)
            elif re.search("^openWB/vehicle/template/chargeTemplate/[1-9]+/chargeMode/pvLoad/.+$", msg.topic) != None:
                if "pv_load" not in self.ev_charge_template_data["ct"+index].data:
                    self.ev_charge_template_data["ct"+index].data["pv_load"]={}
                    if "batPrio" in msg.topic:
                        self.ev_charge_template_data["ct"+index].data["pv_load"]["bat_prio"]=int(msg.payload)
                    elif "feedInLimit" in msg.topic:
                        self.ev_charge_template_data["ct"+index].data["pv_load"]["feed_in_limit"]=int(msg.payload)
                    elif "minCurrent" in msg.topic:
                        self.ev_charge_template_data["ct"+index].data["pv_load"]["min_current"]=int(msg.payload)
                    elif "minSoc" in msg.topic:
                        self.ev_charge_template_data["ct"+index].data["pv_load"]["min_soc"]=int(msg.payload)
                    elif "minSocCurrent" in msg.topic:
                        self.ev_charge_template_data["ct"+index].data["pv_load"]["min_soc_current"]=int(msg.payload)
                    elif "maxSoc" in msg.topic:
                        self.ev_charge_template_data["ct"+index].data["pv_load"]["max_soc"]=int(msg.payload)
            elif re.search("^openWB/vehicle/template/chargeTemplate/[1-9]+/chargeMode/scheduledLoad/.+$", msg.topic) != None:
                if "pv_load" not in self.ev_charge_template_data["ct"+index].data:
                    self.ev_charge_template_data["ct"+index].data["scheduled_load"]={}
                    index_second=re.search(".+/([0-9]+)/.+/([0-9]+)/.+", msg.topic).group(2)
                    if "plan"+index_second not in self.ev_charge_template_data["ct"+index].data["scheduled_load"]:
                        self.ev_charge_template_data["ct"+index].data["scheduled_load"]["plan"+index_second]={}
                    if "frequency" in msg.topic:
                        self.ev_charge_template_data["ct"+index].data["scheduled_load"]["plan"+index_second]["frequency"]=str(msg.payload.decode("utf-8"))
                    elif "once" in msg.topic:
                        self.ev_charge_template_data["ct"+index].data["scheduled_load"]["plan"+index_second]["once"]=str(msg.payload.decode("utf-8"))
                    elif "weekly" in msg.topic:
                        self.ev_charge_template_data["ct"+index].data["scheduled_load"]["plan"+index_second]["weekly"]=str(msg.payload.decode("utf-8"))
                    elif "time" in msg.topic:
                        self.ev_charge_template_data["ct"+index].data["scheduled_load"]["plan"+index_second]["time"]=str(msg.payload.decode("utf-8"))
                    elif "soc" in msg.topic:
                        self.ev_charge_template_data["ct"+index].data["scheduled_load"]["plan"+index_second]["soc"]=int(msg.payload)
            elif re.search("^openWB/vehicle/template/chargeTemplate/[1-9]+/timeLoad$", msg.topic) != None:
                self.ev_charge_template_data["ct"+index].data["time_load"]=int(msg.payload)
            elif re.search("^openWB/vehicle/template/chargeTemplate/[1-9]+/timeLoad/.+$", msg.topic) != None:
                if "pv_load" not in self.ev_charge_template_data["ct"+index].data:
                    self.ev_charge_template_data["ct"+index].data["time_load"]={}
                    index_second=re.search(".+/([0-9]+)/.+/([0-9]+)/.+", msg.topic).group(2)
                    if "plan"+index_second not in self.ev_charge_template_data["ct"+index].data["time_load"]:
                        self.ev_charge_template_data["ct"+index].data["time_load"]["plan"+index_second]={}
                    if "frequency" in msg.topic:
                        self.ev_charge_template_data["ct"+index].data["time_load"]["plan"+index_second]["frequency"]=str(msg.payload.decode("utf-8"))
                    elif "once" in msg.topic:
                        self.ev_charge_template_data["ct"+index].data["time_load"]["plan"+index_second]["once"]=str(msg.payload.decode("utf-8"))
                    elif "weekly" in msg.topic:
                        self.ev_charge_template_data["ct"+index].data["time_load"]["plan"+index_second]["weekly"]=str(msg.payload.decode("utf-8"))
                    elif "time" in msg.topic:
                        self.ev_charge_template_data["ct"+index].data["time_load"]["plan"+index_second]["time"]=str(msg.payload.decode("utf-8"))
                    elif "soc" in msg.topic:
                        self.ev_charge_template_data["ct"+index].data["time_load"]["plan"+index_second]["soc"]=int(msg.payload)
        elif "openWB/vehicle/template/evTemplate" in msg.topic:
            index=self.get_index(msg.topic)
            if "ct"+index not in self.ev_charge_template_data:
                self.ev_template_data["ct"+index] = ev.evTemplate()
            if re.search("^openWB/vehicle/template/evTemplate/[1-9]+/name$", msg.topic) != None:
                self.ev_template_data["ct"+index].data["name"]=str(msg.payload.decode("utf-8"))
            elif re.search("^openWB/vehicle/template/evTemplate/[1-9]+/averageConsump$", msg.topic) != None:
                self.ev_template_data["ct"+index].data["average_consump"]=int(msg.payload)
            elif re.search("^openWB/vehicle/template/evTemplate/[1-9]+/batteryCapcity$", msg.topic) != None:
                self.ev_template_data["ct"+index].data["battery_capcity"]=int(msg.payload)
            elif re.search("^openWB/vehicle/template/evTemplate/[1-9]+/maxPhases$", msg.topic) != None:
                self.ev_template_data["ct"+index].data["max_phases"]=int(msg.payload)
            elif re.search("^openWB/vehicle/template/evTemplate/[1-9]+/minCurrent$", msg.topic) != None:
                self.ev_template_data["ct"+index].data["min_current"]=int(msg.payload)
            elif re.search("^openWB/vehicle/template/evTemplate/[1-9]+/maxCurrent$", msg.topic) != None:
                self.ev_template_data["ct"+index].data["max_current"]=int(msg.payload)
            elif re.search("^openWB/vehicle/template/evTemplate/[1-9]+/controlPilotInterruption$", msg.topic) != None:
                self.ev_template_data["ct"+index].data["control_pilot_interruption"]=int(msg.payload)

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

    #     if topic=="openWB/chargepoint/1":
    #         if payload==True:
    #             cp1=chargepoint()
    #             data.cp_data.append(cp1)
    #         else
    #             data.cp_data[0].remove(cp1)
    #     elif topic == "openWB/chargepoint/1/config/template/autolock":
    #         if cp1 in data.cp_data:
    #             cp1=chargepoint()
    #             data.cp_data.append(cp1)
    #         if payload == True:
    #             data.cp_data[0].autolock=true
    #         else
    #             data.cp_data[0].autolock=false
    #     elif topic=="openWB/chargepoint/1/config/template":
    #         if payload!="none":
    #             data.cp_data[0].template=payload
    #     elif topic="openWB/general/controlInterval":
            
    #         self.ticker_prepare.clear()
    #         seconds = mqttpayload
    #         self.ticker_prepare.set()
    #         while not self.ticker_prepare.wait(seconds):
    #             self.prep.setup_algorithm() 