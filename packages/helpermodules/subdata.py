""" Modul, um die Daten vom Broker zu erhalten.
"""
import importlib
import json
import logging
from pathlib import Path
import paho.mqtt.client as mqtt
import re
import subprocess

from control import bat
from control import chargepoint
from control import counter
from control import ev
from control import general
from helpermodules import graph
from control import optional
from helpermodules.pub import Pub
from helpermodules import system
from control import pv

log = logging.getLogger(__name__)
mqqt_log = logging.getLogger("mqtt")


class SubData:
    """ Klasse, die die benötigten Topics abonniert, die Instanzen ertstellt, wenn z.b. ein Modul neu konfiguriert
    wird, Instanzen löscht, wenn Module gelöscht werden, und die Werte in die Attribute der Instanzen schreibt.
    """

    # Instanzen
    cp_data = {}
    cp_template_data = {}
    pv_data = {}
    ev_data = {}
    ev_template_data = {}
    ev_charge_template_data = {}
    counter_data = {}
    bat_data = {}
    general_data = {}
    optional_data = {}
    system_data = {}
    graph_data = {}

    def __init__(self, event_ev_template, event_charge_template, event_cp_config):
        self.event_ev_template = event_ev_template
        self.event_charge_template = event_charge_template
        self.event_cp_config = event_cp_config
        self.heartbeat = False

        self.bat_data["all"] = bat.BatAll()
        self.cp_data["all"] = chargepoint.AllChargepoints()
        self.counter_data["all"] = counter.CounterAll()
        self.pv_data["all"] = pv.PvAll()
        self.graph_data["graph"] = graph.Graph()

    def sub_topics(self):
        """ abonniert alle Topics.
        """
        try:
            mqtt_broker_ip = "localhost"
            self.client = mqtt.Client("openWB-mqttsub-" + self.getserial())
            # ipallowed='^[0-9.]+$'
            # nameallowed='^[a-zA-Z ]+$'
            # namenumballowed='^[0-9a-zA-Z ]+$'

            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.connect(mqtt_broker_ip, 1886)
            self.client.loop_forever()
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def disconnect(self) -> None:
        self.client.disconnect()
        log.info("Verbindung von Client openWB-mqttsub-" + self.getserial()+" geschlossen.")

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
        client.subscribe("openWB/vehicle/#", 2)
        client.subscribe("openWB/chargepoint/#", 2)
        client.subscribe("openWB/pv/#", 2)
        client.subscribe("openWB/bat/#", 2)
        client.subscribe("openWB/general/#", 2)
        client.subscribe("openWB/graph/#", 2)
        client.subscribe("openWB/optional/#", 2)
        client.subscribe("openWB/counter/#", 2)
        # Nicht mit wildcard abonnieren, damit nicht die Komponenten vor den Devices empfangen werden.
        client.subscribe("openWB/system/+", 2)
        client.subscribe("openWB/system/mqtt/bridge/+", 2)
        client.subscribe("openWB/system/device/+/config", 2)

    def on_message(self, client, userdata, msg):
        """ wartet auf eingehende Topics.
        """
        mqqt_log.debug("Topic: "+str(msg.topic) +
                       ", Payload: "+str(msg.payload.decode("utf-8")))
        self.heartbeat = True
        if "openWB/vehicle/template/charge_template/" in msg.topic:
            self.process_vehicle_charge_template_topic(
                self.ev_charge_template_data, msg)
        elif "openWB/vehicle/template/ev_template/" in msg.topic:
            self.process_vehicle_ev_template_topic(self.ev_template_data, msg)
        elif "openWB/vehicle/" in msg.topic:
            self.process_vehicle_topic(self.ev_data, msg)
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
        elif "openWB/optional/" in msg.topic:
            self.process_optional_topic(self.optional_data, msg)
        elif "openWB/counter/" in msg.topic:
            self.process_counter_topic(self.counter_data, msg)
        elif "openWB/system/" in msg.topic:
            self.process_system_topic(client, self.system_data, msg)
        else:
            log.warning("unknown subdata-topic: "+str(msg.topic))

    def get_index(self, topic):
        """extrahiert den Index aus einem Topic (Zahl zwischen zwei // oder am Stringende)

         Parameters
        ----------
        topic : str
            Topic, aus dem der Index extrahiert wird
        """
        index = re.search('(?!/)([0-9]*)(?=/|$)', topic)
        return index.group()

    def get_second_index(self, topic):
        """extrahiert den zweiten Index aus einem Topic (Zahl zwischen zwei //)

            Parameters
        ----------
        topic : str
            Topic, aus dem der Index extrahiert wird
        """
        index = re.search('^.+/([0-9]*)/.+/([0-9]+)/*.*$', topic)
        return index.group(2)

    def set_json_payload(self, dict, msg):
        """ dekodiert das JSON-Objekt und setzt diesen für den Value in das übergebene Dictionary, als Key wird der
        Name nach dem letzten / verwendet.

         Parameters
        ----------
        dict : dictionary
            Dictionary, in dem der Wert abgelegt wird
        msg :
            enthält den Payload als json-Objekt
        """
        try:
            key = re.search("/([a-z,A-Z,0-9,_]+)(?!.*/)", msg.topic).group(1)
            if msg.payload:
                dict[key] = json.loads(str(msg.payload.decode("utf-8")))
            else:
                if key in dict:
                    dict.pop(key)
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_vehicle_topic(self, var, msg):
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
            index = self.get_index(msg.topic)
            if re.search("^.+/vehicle/[0-9]+/.+$", msg.topic) is not None:
                if str(msg.payload.decode("utf-8")) == "":
                    if re.search("^.+/vehicle/[0-9]+/soc_module/config$", msg.topic) is not None:
                        var["ev"+index].soc_module = None
                    elif re.search("^.+/vehicle/[0-9]+/get.+$", msg.topic) is not None:
                        self.set_json_payload(var["ev"+index].data["get"], msg)
                    else:
                        if "ev"+index in var:
                            var.pop("ev"+index)
                else:
                    if "ev"+index not in var:
                        var["ev"+index] = ev.Ev(int(index))

                    if re.search("^.+/vehicle/[0-9]+/get.+$", msg.topic) is not None:
                        if "get" not in var["ev"+index].data:
                            var["ev"+index].data["get"] = {}
                        self.set_json_payload(var["ev"+index].data["get"], msg)
                    elif re.search("^.+/vehicle/[0-9]+/set.+$", msg.topic) is not None:
                        if "set" not in var["ev"+index].data:
                            var["ev"+index].data["set"] = {}
                        self.set_json_payload(var["ev"+index].data["set"], msg)
                    elif re.search("^.+/vehicle/[0-9]+/soc_module/config$", msg.topic) is not None:
                        config = json.loads(str(msg.payload.decode("utf-8")))
                        if config["type"] is None:
                            var["ev"+index].soc_module = None
                        else:
                            mod = importlib.import_module("."+config["type"]+".soc", "modules")
                            var["ev"+index].soc_module = mod.Soc(config)
                    elif re.search("^.+/vehicle/[0-9]+/control_parameter/.+$", msg.topic) is not None:
                        if "control_parameter" not in var["ev"+index].data:
                            var["ev"+index].data["control_parameter"] = {}
                        self.set_json_payload(
                            var["ev"+index].data["control_parameter"], msg)
                    else:
                        self.set_json_payload(var["ev"+index].data, msg)
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_vehicle_charge_template_topic(self, var, msg):
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
            index = self.get_index(msg.topic)
            if str(msg.payload.decode("utf-8")) == "":
                if "ct"+index in var:
                    var.pop("ct"+index)
            else:
                if "ct"+index not in var:
                    var["ct"+index] = ev.ChargeTemplate(int(index))
                if re.search("^.+/vehicle/template/charge_template/[0-9]+/chargemode/scheduled_charging/plans/[0-9]+$",
                             msg.topic) is not None:
                    index_second = self.get_second_index(msg.topic)
                    if str(msg.payload.decode("utf-8")) == "":
                        if "ct"+index in var["ct"+index].data["chargemode"]["scheduled_charging"]["plans"]:
                            var.pop("ct"+index)
                        else:
                            log.error("Es konnte kein Zielladen-Plan mit der ID " +
                                      str(index_second)+" in der Ladevorlage "+str(index)+" gefunden werden.")
                    else:
                        var["ct"+index].data["chargemode"]["scheduled_charging"]["plans"][str(
                            index)] = json.loads(str(msg.payload.decode("utf-8")))
                elif re.search("^.+/vehicle/template/charge_template/[0-9]+/time_charging/plans/[0-9]+$",
                               msg.topic) is not None:
                    index_second = self.get_second_index(msg.topic)
                    if str(msg.payload.decode("utf-8")) == "":
                        if "ct"+index in var["ct"+index].data["time_charging"]["plans"]:
                            var.pop("ct"+index)
                        else:
                            log.error("Es konnte kein Zeitladen-Plan mit der ID " +
                                      str(index_second)+" in der Ladevorlage "+str(index)+" gefunden werden.")
                    else:
                        var["ct"+index].data["time_charging"]["plans"][str(
                            index)] = json.loads(str(msg.payload.decode("utf-8")))
                else:
                    # Pläne unverändert übernehmen
                    scheduled_charging_plans = var["ct" + index].data["chargemode"]["scheduled_charging"]["plans"]
                    time_charging_plans = var["ct" + index].data["time_charging"]["plans"]
                    var["ct" + index].data = json.loads(str(msg.payload.decode("utf-8")))
                    var["ct"+index].data["time_charging"]["plans"] = time_charging_plans
                    var["ct"+index].data["chargemode"]["scheduled_charging"]["plans"] = scheduled_charging_plans
                    self.event_charge_template.set()
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_vehicle_ev_template_topic(self, var, msg):
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
            index = self.get_index(msg.topic)
            if re.search("^.+/vehicle/template/ev_template/[0-9]+$", msg.topic) is not None:
                if str(msg.payload.decode("utf-8")) == "":
                    if "et"+index in var:
                        var.pop("et"+index)
                else:
                    if "et"+index not in var:
                        var["et"+index] = ev.EvTemplate(int(index))
                    var["et" + index].data = json.loads(str(msg.payload.decode("utf-8")))
                    self.event_ev_template.set()
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_chargepoint_topic(self, var, msg):
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
            if re.search("^.+/chargepoint/[0-9]+/.+$", msg.topic) is not None:
                index = self.get_index(msg.topic)
                if str(msg.payload.decode("utf-8")) == "":
                    if "cp"+index in var:
                        var.pop("cp"+index)
                else:
                    if "cp"+index not in var:
                        var["cp"+index] = chargepoint.Chargepoint(int(index))
                    if re.search("^.+/chargepoint/[0-9]+/set/.+$", msg.topic) is not None:
                        if "set" not in var["cp"+index].data:
                            var["cp"+index].data["set"] = {}
                        if re.search("^.+/chargepoint/[0-9]+/set/log/.+$", msg.topic) is not None:
                            if "log" not in var["cp"+index].data["set"]:
                                var["cp"+index].data["set"]["log"] = {}
                            self.set_json_payload(
                                var["cp"+index].data["set"]["log"], msg)
                        else:
                            self.set_json_payload(var["cp"+index].data["set"], msg)
                    elif re.search("^.+/chargepoint/[0-9]+/get/.+$", msg.topic) is not None:
                        if "get" not in var["cp"+index].data:
                            var["cp"+index].data["get"] = {}
                        if re.search("^.+/chargepoint/[0-9]+/get/connected_vehicle/.+$", msg.topic) is not None:
                            if "connected_vehicle" not in var["cp"+index].data["get"]:
                                var["cp"+index].data["get"]["connected_vehicle"] = {}
                            self.set_json_payload(
                                var["cp"+index].data["get"]["connected_vehicle"], msg)
                        elif re.search("^.+/chargepoint/[0-9]+/get/.+$", msg.topic) is not None:
                            self.set_json_payload(var["cp"+index].data["get"], msg)
                    elif re.search("^.+/chargepoint/[0-9]+/config$", msg.topic) is not None:
                        config = json.loads(
                            str(msg.payload.decode("utf-8")))
                        if (var["cp"+index].chargepoint_module is None or
                                config["connection_module"] != var["cp"+index].chargepoint_module.connection_module or
                                config["power_module"] != var["cp"+index].chargepoint_module.power_module):
                            mod = importlib.import_module(
                                "."+config["connection_module"]["type"]+".chargepoint_module", "modules")
                            var["cp"+index].chargepoint_module = mod.ChargepointModule(
                                config["id"], config["connection_module"], config["power_module"])
                        self.set_json_payload(var["cp"+index].data, msg)
                        self.event_cp_config.set()
            elif re.search("^.+/chargepoint/get/.+$", msg.topic) is not None:
                self.set_json_payload(var["all"].data["get"], msg)
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_chargepoint_template_topic(self, var, msg):
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
            index = self.get_index(msg.topic)
            if json.loads(str(msg.payload.decode("utf-8"))):
                if "cpt"+index not in var:
                    var["cpt"+index] = chargepoint.CpTemplate()
            else:
                if "cpt"+index in var:
                    var.pop("cpt"+index)
            if re.search("^.+/chargepoint/template/[0-9]+/autolock/.+$", msg.topic) is not None:
                if "autolock" not in var["cpt"+index].data:
                    var["cpt"+index].data["autolock"] = {}
                index_second = self.get_second_index(msg.topic)
                if "plan"+index_second not in var["cpt"+index].data["autolock"]:
                    if "plans" not in var["cpt"+index].data["autolock"]:
                        var["cpt"+index].data["autolock"]["plans"] = {}
                    self.set_json_payload(
                        var["cpt"+index].data["autolock"]["plans"], msg)
            else:
                autolock_plans = var["cpt"+index].data["autolock"]["plans"]
                var["cpt" + index].data = json.loads(str(msg.payload.decode("utf-8")))
                var["cpt"+index].data["autolock"]["plans"] = autolock_plans

        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_pv_topic(self, var, msg):
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
            if re.search("^.+/pv/[0-9]+/.+$", msg.topic) is not None:
                index = self.get_index(msg.topic)
                if str(msg.payload.decode("utf-8")) == "":
                    if "pv"+index in var:
                        var.pop("pv"+index)
                else:
                    if "pv"+index not in var:
                        var["pv"+index] = pv.Pv(int(index))
                    if re.search("^.+/pv/[0-9]+/config/.+$", msg.topic) is not None:
                        self.set_json_payload(var["pv"+index].data["config"], msg)
                    elif re.search("^.+/pv/[0-9]+/get/.+$", msg.topic) is not None:
                        self.set_json_payload(var["pv"+index].data["get"], msg)
            elif re.search("^.+/pv/.+$", msg.topic) is not None:
                if re.search("^.+/pv/config/.+$", msg.topic) is not None:
                    if "config" not in var["all"].data:
                        var["all"].data["config"] = {}
                    self.set_json_payload(var["all"].data["config"], msg)
                elif re.search("^.+/pv/get/.+$", msg.topic) is not None:
                    if "get" not in var["all"].data:
                        var["all"].data["get"] = {}
                    self.set_json_payload(var["all"].data["get"], msg)
                elif re.search("^.+/pv/set/.+$", msg.topic) is not None:
                    if "set" not in var["all"].data:
                        var["all"].data["set"] = {}
                    self.set_json_payload(var["all"].data["set"], msg)
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_bat_topic(self, var, msg):
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
            if re.search("^.+/bat/[0-9]+/.+$", msg.topic) is not None:
                index = self.get_index(msg.topic)
                if str(msg.payload.decode("utf-8")) == "":
                    if "bat"+index in var:
                        var.pop("bat"+index)
                else:
                    if "bat"+index not in var:
                        var["bat"+index] = bat.Bat(int(index))
                    if re.search("^.+/bat/[0-9]+/config$", msg.topic) is not None:
                        self.set_json_payload(var["bat"+index].data, msg)
                    elif re.search("^.+/bat/[0-9]+/get/.+$", msg.topic) is not None:
                        if "get" not in var["bat"+index].data:
                            var["bat"+index].data["get"] = {}
                        self.set_json_payload(var["bat"+index].data["get"], msg)
                    elif re.search("^.+/bat/[0-9]+/set/.+$", msg.topic) is not None:
                        if "set" not in var["bat"+index].data:
                            var["bat"+index].data["set"] = {}
                        self.set_json_payload(var["bat"+index].data["set"], msg)
            elif re.search("^.+/bat/.+$", msg.topic) is not None:
                if re.search("^.+/bat/get/.+$", msg.topic) is not None:
                    if "get" not in var["all"].data:
                        var["all"].data["get"] = {}
                    self.set_json_payload(var["all"].data["get"], msg)
                elif re.search("^.+/bat/set/.+$", msg.topic) is not None:
                    if "set" not in var["all"].data:
                        var["all"].data["set"] = {}
                    self.set_json_payload(var["all"].data["set"], msg)
                elif re.search("^.+/bat/config/.+$", msg.topic) is not None:
                    if "config" not in var["all"].data:
                        var["all"].data["config"] = {}
                    self.set_json_payload(var["all"].data["config"], msg)
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_general_topic(self, var, msg):
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
            if re.search("^.+/general/.+$", msg.topic) is not None:
                if "general" not in var:
                    var["general"] = general.General()
                if re.search("^.+/general/notifications/.+$", msg.topic) is not None:
                    if "notifications" not in var["general"].data:
                        var["general"].data["notifications"] = {}
                    self.set_json_payload(
                        var["general"].data["notifications"], msg)
                elif re.search("^.+/general/ripple_control_receiver/.+$", msg.topic) is not None:
                    if "ripple_control_receiver" not in var["general"].data:
                        var["general"].data["ripple_control_receiver"] = {}
                    self.set_json_payload(
                        var["general"].data["ripple_control_receiver"], msg)
                elif re.search("^.+/general/chargemode_config/.+$", msg.topic) is not None:
                    if "chargemode_config" not in var["general"].data:
                        var["general"].data["chargemode_config"] = {}
                    if re.search("^.+/general/chargemode_config/pv_charging/.+$", msg.topic) is not None:
                        if "pv_charging" not in var["general"].data["chargemode_config"]:
                            var["general"].data["chargemode_config"]["pv_charging"] = {}
                        self.set_json_payload(
                            var["general"].data["chargemode_config"]["pv_charging"], msg)
                    elif re.search("^.+/general/chargemode_config/instant_charging/.+$", msg.topic) is not None:
                        if "instant_charging" not in var["general"].data["chargemode_config"]:
                            var["general"].data["chargemode_config"]["instant_charging"] = {}
                        self.set_json_payload(
                            var["general"].data["chargemode_config"]["instant_charging"], msg)
                    elif re.search("^.+/general/chargemode_config/scheduled_charging/.+$", msg.topic) is not None:
                        if "scheduled_charging" not in var["general"].data["chargemode_config"]:
                            var["general"].data["chargemode_config"]["scheduled_charging"] = {}
                        self.set_json_payload(
                            var["general"].data["chargemode_config"]["scheduled_charging"], msg)
                    elif re.search("^.+/general/chargemode_config/time_charging/.+$", msg.topic) is not None:
                        if "time_charging" not in var["general"].data["chargemode_config"]:
                            var["general"].data["chargemode_config"]["time_charging"] = {}
                        self.set_json_payload(
                            var["general"].data["chargemode_config"]["time_charging"], msg)
                    elif re.search("^.+/general/chargemode_config/standby/.+$", msg.topic) is not None:
                        if "standby" not in var["general"].data["chargemode_config"]:
                            var["general"].data["chargemode_config"]["standby"] = {}
                        self.set_json_payload(
                            var["general"].data["chargemode_config"]["standby"], msg)
                    else:
                        self.set_json_payload(
                            var["general"].data["chargemode_config"], msg)
                else:
                    self.set_json_payload(var["general"].data, msg)
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_optional_topic(self, var, msg):
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
            if re.search("^.+/optional/.+$", msg.topic) is not None:
                if "optional" not in var:
                    var["optional"] = optional.Optional()
                if re.search("^.+/optional/led/.+$", msg.topic) is not None:
                    if "led" not in var["optional"].data:
                        var["optional"].data["led"] = {}
                    self.set_json_payload(var["optional"].data["led"], msg)
                elif re.search("^.+/optional/rfid/.+$", msg.topic) is not None:
                    if "rfid" not in var["optional"].data:
                        var["optional"].data["rfid"] = {}
                    self.set_json_payload(var["optional"].data["rfid"], msg)
                elif re.search("^.+/optional/int_display/.+$", msg.topic) is not None:
                    if "int_display" not in var["optional"].data:
                        var["optional"].data["int_display"] = {}
                    self.set_json_payload(
                        var["optional"].data["int_display"], msg)
                elif re.search("^.+/optional/et/.+$", msg.topic) is not None:
                    if "et" not in var["optional"].data:
                        var["optional"].data["et"] = {}
                    if re.search("^.+/optional/et/get/.+$", msg.topic) is not None:
                        if "get" not in var["optional"].data["et"]:
                            var["optional"].data["et"]["get"] = {}
                        self.set_json_payload(
                            var["optional"].data["et"]["get"], msg)
                    elif re.search("^.+/optional/et/config/.+$", msg.topic) is not None:
                        if "config" not in var["optional"].data["et"]:
                            var["optional"].data["et"]["config"] = {}
                        self.set_json_payload(
                            var["optional"].data["et"]["config"], msg)
                    else:
                        self.set_json_payload(var["optional"].data["et"], msg)
                else:
                    self.set_json_payload(var["optional"].data, msg)
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_counter_topic(self, var, msg):
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
            if re.search("^.+/counter/[0-9]+/.+$", msg.topic) is not None:
                index = self.get_index(msg.topic)
                if str(msg.payload.decode("utf-8")) == "":
                    if "counter"+index in var:
                        var.pop("counter"+index)
                else:
                    if "counter"+index not in var:
                        var["counter"+index] = counter.Counter(int(index))
                    if re.search("^.+/counter/[0-9]+/get.+$", msg.topic) is not None:
                        if "get" not in var["counter"+index].data:
                            var["counter"+index].data["get"] = {}
                        self.set_json_payload(
                            var["counter"+index].data["get"], msg)
                    elif re.search("^.+/counter/[0-9]+/set.+$", msg.topic) is not None:
                        if "set" not in var["counter"+index].data:
                            var["counter"+index].data["set"] = {}
                        self.set_json_payload(
                            var["counter"+index].data["set"], msg)
                    elif re.search("^.+/counter/[0-9]+/config/.+$", msg.topic) is not None:
                        if "config" not in var["counter"+index].data:
                            var["counter"+index].data["config"] = {}
                        self.set_json_payload(
                            var["counter"+index].data["config"], msg)
            elif re.search("^.+/counter/.+$", msg.topic) is not None:
                if re.search("^.+/counter/get.+$", msg.topic) is not None:
                    if "get" not in var["all"].data:
                        var["all"].data["get"] = {}
                    self.set_json_payload(var["all"].data["get"], msg)
                elif re.search("^.+/counter/set.+$", msg.topic) is not None:
                    if "set" not in var["all"].data:
                        var["all"].data["set"] = {}
                    self.set_json_payload(var["all"].data["set"], msg)
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_system_topic(self, client, var, msg):
        """Handler für die System-Topics

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
            if "system" not in var:
                if str(msg.payload.decode("utf-8")) == "":
                    if "system" in var:
                        var.pop("system")
                else:
                    var["system"] = system.System()
            if re.search("^.+/device/[0-9]+/config$", msg.topic) is not None:
                index = self.get_index(msg.topic)
                if str(msg.payload.decode("utf-8")) == "":
                    if "device"+index in var:
                        var.pop("device"+index)
                    else:
                        log.error("Es konnte kein Device mit der ID " +
                                  str(index)+" gefunden werden.")
                else:
                    device_config = json.loads(
                        str(msg.payload.decode("utf-8")))
                    dev = importlib.import_module(
                        "."+device_config["type"]+".device", "modules")
                    var["device"+index] = dev.Device(device_config)
                    # Durch das erneute Subscriben werden die Komponenten mit dem aktualisierten TCP-Client angelegt.
                    client.subscribe("openWB/system/device/" +
                                     index+"/component/#", 2)
            elif re.search("^.+/device/[0-9]+/get$", msg.topic) is not None:
                index = self.get_index(msg.topic)
                if "get" not in var["device"+index].data:
                    var["device"+index].data["get"] = {}
                self.set_json_payload(var["device"+index].data["get"], msg)
            elif re.search("^.+/device/[0-9]+/component/[0-9]+/simulation/.+$", msg.topic) is not None:
                index = self.get_index(msg.topic)
                index_second = self.get_second_index(msg.topic)
                self.set_json_payload(
                    var["device"+index].components["component"+index_second].simulation, msg)
            elif re.search("^.+/device/[0-9]+/component/[0-9]+/config$", msg.topic) is not None:
                index = self.get_index(msg.topic)
                index_second = self.get_second_index(msg.topic)
                if str(msg.payload.decode("utf-8")) == "":
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
                    try:
                        sim_data = var["device"+index].components["component" + index_second].simulation
                    except (KeyError, AttributeError):
                        sim_data = None
                    # Es darf nicht einfach data["config"] aktualisiert werden, da in der __init__ auch die
                    # TCP-Verbindung aufgebaut wird, deren IP dann nicht aktualisiert werden würde.
                    var["device"+index].add_component(
                        json.loads(str(msg.payload.decode("utf-8"))))
                    if sim_data:
                        var["device"+index].components["component" + index_second].simulation = sim_data
            elif "mqtt" and "bridge" in msg.topic:
                index = self.get_index(msg.topic)
                parent_file = Path(__file__).resolve().parents[2]
                subprocess.call(["php", "-f", str(parent_file / "runs" / "savemqtt.php"), index, msg.payload])
            elif "GetRemoteSupport" in msg.topic:
                payload = json.loads(str(msg.payload.decode("utf-8")))
                splitted = payload.split(";")
                token = splitted[0]
                port = splitted[1]
                if len(splitted) == 3:
                    user = splitted[2]
                else:
                    user = "getsupport"
                subprocess.run([str(Path(__file__).resolve().parents[2] / "runs" / "start_remote_support.sh"),
                                token, port, user])
            else:
                self.set_json_payload(var["system"].data, msg)
        except Exception:
            log.exception("Fehler im subdata-Modul")

    def process_graph_topic(self, var, msg):
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
            if re.search("^.+/graph/.+$", msg.topic) is not None:
                if re.search("^.+/graph/config/.+$", msg.topic) is not None:
                    if "config" not in var["graph"].data:
                        var["graph"].data["config"] = {}
                    self.set_json_payload(var["graph"].data["config"], msg)
        except Exception:
            log.exception("Fehler im subdata-Modul")
