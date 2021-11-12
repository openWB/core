"""verarbeitet Befehl vom Broker
"""

import importlib
import json
import paho.mqtt.client as mqtt
import re
import time
import traceback

from . import log
from . import pub
from ..algorithm import chargepoint
from ..algorithm import data
from ..algorithm import ev


class Command:
    """
    """

    def __init__(self):
        try:
            self.__get_max_id(
                "autolock_plan", "chargepoint/template/+/autolock")
            self.__get_max_id("charge_template",
                              "vehicle/template/charge_template")
            self.__get_max_id("charge_template_scheduled_plan",
                              "vehicle/template/charge_template/+/chargemode/scheduled_charging/plans/")
            self.__get_max_id("charge_template_time_charging_plan",
                              "vehicle/template/charge_template/+/chargemode/time_charging/plans/")
            self.__get_max_id("chargepoint", "chargepoint")
            self.__get_max_id("chargepoint_template", "chargepoint/template")
            self.__get_max_id("component", "system/device/+/component")
            self.__get_max_id("device", "system/device")
            self.__get_max_id("ev_template", "vehicle/template/ev_template")
            self.__get_max_id("vehicle", "vehicle")
        except Exception:
            log.MainLogger().exception("Fehler im Command-Modul")

    def __get_max_id(self, id_topic: str, topic: str) -> None:
        """ ermittelt die maximale ID vom Broker """
        try:
            max_id = ProcessBrokerBranch(topic).get_max_id()
            pub.pub("openWB/set/command/max_id/"+id_topic, max_id)
        except Exception:
            log.MainLogger().exception("Fehler im Command-Modul")

    def sub_commands(self):
        """ abonniert alle Topics.
        """
        try:
            # kurze Pause, damit die ID vom Broker ermittelt werden können. Sonst werden noch vorher die retained Topics empfangen, was zu doppelten Logmeldungen führt.
            time.sleep(1)
            mqtt_broker_ip = "localhost"
            client = mqtt.Client("openWB-command-" + str(self.getserial()))

            client.on_connect = self.on_connect
            client.on_message = self.on_message

            client.connect(mqtt_broker_ip, 1886)
            client.loop_forever()
            client.disconnect()
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def getserial(self):
        """ Extract serial from cpuinfo file
        """
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line[0:6] == 'Serial':
                        return line[10:26]
                return "0000000000000000"
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def on_connect(self, client, userdata, flags, rc):
        """ connect to broker and subscribe to set topics
        """
        try:
            client.subscribe("openWB/command/#", 2)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def on_message(self, client, userdata, msg):
        """ wartet auf eingehende Topics.
        """
        try:
            if str(msg.payload.decode("utf-8")) != '':
                if "todo" in msg.topic:
                    payload = json.loads(str(msg.payload.decode("utf-8")))
                    connection_id = msg.topic.split("/")[2]
                    # Methoden-Name = Befehl
                    try:
                        func = getattr(self, payload["command"])
                        func(connection_id, payload)
                    except Exception:
                        log.MainLogger().error("Zu dem Befehl wurde keine Methode gefunden.")
                        self.__pub_error(
                            payload, connection_id, "Zu dem Befehl wurde keine Methode gefunden.")
                    pub.pub(msg.topic, "")
                elif "max_id" in msg.topic:
                    self.__process_max_id_topic(msg)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def __process_max_id_topic(self, msg, no_log: bool = False) -> None:
        try:
            payload = json.loads(str(msg.payload.decode("utf-8")))
            var = re.search("/([a-z,A-Z,0-9,_]+)(?!.*/)", msg.topic).group(1)
            # Der Variablen-Name für die maximale ID setzt sich aus "max_id_" und dem Topic-Namen nach dem letzten / zusammen.
            setattr(self, "max_id_"+var, payload)
            log.MainLogger().debug("Max ID "+var+" "+str(payload))
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def __pub_error(self, payload: dict, connection_id: str, error_str: str) -> None:
        """ sendet ein Fehler-Topic, warum der Befehl nicht ausgeführt werden konnte.
        """
        try:
            error_payload = {
                "command": payload["command"],
                "data": payload["data"],
                "error": error_str
            }
            pub.pub("openWB/set/command/" +
                    str(connection_id)+"/error", error_payload)
            log.MainLogger().error("Befehl konnte nicht ausgefuehrt werden: "+str(error_payload))
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def addDevice(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neues Device erstellt werden soll.
        """
        try:
            new_id = self.max_id_device + 1
            log.MainLogger().info("Neues Device vom Typ" +
                                  str(payload["data"]["type"])+" mit ID "+str(new_id)+" hinzugefuegt.")
            dev = importlib.import_module(
                ".modules."+payload["data"]["type"]+".device", "packages")
            device_default = dev.get_default()
            device_default["id"] = new_id
            pub.pub("openWB/set/system/device/" +
                    str(new_id)+"/config", device_default)
            self.max_id_device = self.max_id_device + 1
            pub.pub("openWB/set/command/max_id/device", self.max_id_device)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(
                payload, connection_id, "Es ist ein interner Fehler aufgetreten: "+traceback.format_exc())

    def removeDevice(self, connection_id: str, payload: dict) -> None:
        """ löscht ein Device.
        """
        try:
            if self.max_id_device >= payload["data"]["id"]:
                log.MainLogger().info("Device mit ID " +
                                      str(payload["data"]["id"])+" geloescht.")
                ProcessBrokerBranch(
                    "system/device/"+str(payload["data"]["id"])).remove_topics()
            else:
                self.__pub_error(
                    payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(
                payload, connection_id, "Es ist ein interner Fehler aufgetreten: "+traceback.format_exc())

    def addChargepoint(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neuer Chargepoint erstellt werden soll.
        """
        try:
            new_id = self.max_id_chargepoint + 1
            log.MainLogger().info("Neuer Ladepunkt vom Typ" +
                                  str(payload["data"]["type"])+" mit ID "+str(new_id)+" hinzugefuegt.")
            chargepoint_default = chargepoint.get_chargepoint_default()
            chargepoint_default["id"] = new_id
            data.data.counter_data["all"].hierarchy_add_item_below(
                "cp"+str(new_id), data.data.counter_data["all"].data["get"]["hierarchy"][0]["id"])
            pub.pub("openWB/set/chargepoint/"+str(new_id) +
                    "/config", chargepoint_default)
            self.max_id_chargepoint = self.max_id_chargepoint + 1
            pub.pub("openWB/set/command/max_id/chargepoint",
                    self.max_id_chargepoint)
            if self.max_id_chargepoint_template == -1:
                self.addChargepointTemplate("addChargepoint", {})
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(
                payload, connection_id, "Es ist ein interner Fehler aufgetreten: "+traceback.format_exc())

    def removeChargepoint(self, connection_id: str, payload: dict) -> None:
        """ löscht ein Chargepoint.
        """
        try:
            if self.max_id_chargepoint >= payload["data"]["id"]:
                data.data.counter_data["all"].hierarchy_remove_item(
                    "cp"+str(payload["data"]["id"]))
                log.MainLogger().info("Ladepunkt mit ID " +
                                      str(payload["data"]["id"])+" geloescht.")
                ProcessBrokerBranch(
                    "chargepoint/"+str(payload["data"]["id"])).remove_topics()
            else:
                self.__pub_error(
                    payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(
                payload, connection_id, "Es ist ein interner Fehler aufgetreten: "+traceback.format_exc())

    def addChargepointTemplate(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem eine neue Ladepunkt-Vorlage erstellt werden soll.
        """
        try:
            new_id = self.max_id_chargepoint_template + 1
            log.MainLogger().info("Neue Ladepunkt-Vorlage mit ID "+str(new_id)+" hinzugefuegt.")
            default = chargepoint.get_chargepoint_template_default()
            default["id"] = new_id
            pub.pub("openWB/set/chargepoint/template/"+str(new_id), default)
            self.max_id_chargepoint_template = self.max_id_chargepoint_template + 1
            pub.pub("openWB/set/command/max_id/chargepoint_template",
                    self.max_id_chargepoint_template)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(
                payload, connection_id, "Es ist ein interner Fehler aufgetreten: "+traceback.format_exc())

    def removeChargepointTemplate(self, connection_id: str, payload: dict) -> None:
        """ löscht eine ladepunkt-Vorlage.
        """
        try:
            if self.max_id_chargepoint_template >= payload["data"]["id"]:
                log.MainLogger().info("Ladepunkt-Vorlage mit ID " +
                                      str(payload["data"]["id"])+" geloescht.")
                ProcessBrokerBranch("chargepoint/template/" +
                                    str(payload["data"]["id"])).remove_topics()
            else:
                self.__pub_error(
                    payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(
                payload, connection_id, "Es ist ein interner Fehler aufgetreten: "+traceback.format_exc())

    def addAutolockPlan(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neuer Zielladen-Plan erstellt werden soll.
        """
        try:
            new_id = self.max_id_autolock_plan + 1
            log.MainLogger().info("Neuer Autolock-Plan mit ID "+str(new_id) +
                                  " zu Template "+str(payload["data"]["template"])+" hinzugefuegt.")
            default = chargepoint.get_autolock_plan_default()
            pub.pub("openWB/set/chargepoint/template/" +
                    str(payload["data"]["template"])+"/autolock/"+str(new_id), default)
            self.max_id_autolock_plan = new_id
            pub.pub("openWB/set/command/max_id/autolock_plan", new_id)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(
                payload, connection_id, "Es ist ein interner Fehler aufgetreten: "+traceback.format_exc())

    def removeAutolockPlan(self, connection_id: str, payload: dict) -> None:
        """ löscht einen Zielladen-Plan.
        """
        try:
            if self.max_id_autolock_plan >= payload["data"]["plan"]:
                log.MainLogger().info("Autolock-Plan mit ID " +
                                      str(payload["data"]["plan"])+" zu Template "+str(payload["data"]["template"])+" geloescht.")
                pub.pub("openWB/chargepoint/template/"+str(
                    payload["data"]["template"])+"/autolock/"+str(payload["data"]["plan"]), "")
            else:
                self.__pub_error(
                    payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(
                payload, connection_id, "Es ist ein interner Fehler aufgetreten: "+traceback.format_exc())

    def addChargeTemplate(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem eine neue Lade-Vorlage erstellt werden soll.
        """
        try:
            new_id = self.max_id_charge_template + 1
            log.MainLogger().info("Neues Lade-Template mit ID "+str(new_id)+" hinzugefuegt.")
            charge_template_default = ev.get_charge_template_default()
            pub.pub("openWB/set/vehicle/template/charge_template/" +
                    str(new_id), charge_template_default)
            self.max_id_charge_template = new_id
            pub.pub("openWB/set/command/max_id/charge_template", new_id)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(
                payload, connection_id, "Es ist ein interner Fehler aufgetreten: "+traceback.format_exc())

    def removeChargeTemplate(self, connection_id: str, payload: dict) -> None:
        """ löscht eine Lade-Vorlage.
        """
        try:
            if self.max_id_charge_template >= payload["data"]["id"]:
                log.MainLogger().info("Lade-Template mit ID " +
                                      str(payload["data"]["id"])+" geloescht.")
                pub.pub("openWB/vehicle/template/charge_template/" +
                        str(payload["data"]["id"]), "")
            else:
                self.__pub_error(
                    payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(
                payload, connection_id, "Es ist ein interner Fehler aufgetreten: "+traceback.format_exc())

    def addChargeTemplateSchedulePlan(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neuer Zielladen-Plan erstellt werden soll.
        """
        try:
            new_id = self.max_id_charge_template_scheduled_plan + 1
            log.MainLogger().info("Neues Zielladen-Template mit ID "+str(new_id) +
                                  " zu Template "+str(payload["data"]["template"])+" hinzugefuegt.")
            charge_template_default = ev.get_charge_template_scheduled_plan_default()
            pub.pub("openWB/set/vehicle/template/charge_template/"+str(
                payload["data"]["template"])+"/chargemode/scheduled_charging/plans/"+str(new_id), charge_template_default)
            self.max_id_charge_template_scheduled_plan = new_id
            pub.pub(
                "openWB/set/command/max_id/charge_template_scheduled_plan", new_id)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(
                payload, connection_id, "Es ist ein interner Fehler aufgetreten: "+traceback.format_exc())

    def removeChargeTemplateSchedulePlan(self, connection_id: str, payload: dict) -> None:
        """ löscht einen Zielladen-Plan.
        """
        try:
            if self.max_id_charge_template_scheduled_plan >= payload["data"]["plan"]:
                log.MainLogger().info("Zielladen-Template mit ID " +
                                      str(payload["data"]["plan"])+" zu Template "+str(payload["data"]["template"])+" geloescht.")
                pub.pub("openWB/vehicle/template/charge_template/"+str(
                    payload["data"]["template"])+"/chargemode/scheduled_charging/plans/"+str(payload["data"]["plan"]), "")
            else:
                self.__pub_error(
                    payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(
                payload, connection_id, "Es ist ein interner Fehler aufgetreten: "+traceback.format_exc())

    def addChargeTemplateTimeChargingPlan(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neuer Zeitladen-Plan erstellt werden soll.
        """
        try:
            new_id = self.max_id_charge_template_time_charging_plan + 1
            log.MainLogger().info("Neues Zeitladen-Template mit ID "+str(new_id) +
                                  " zu Template "+str(payload["data"]["template"])+" hinzugefuegt.")
            time_charging_plan_default = ev.get_charge_template_time_charging_plan_default()
            pub.pub("openWB/set/vehicle/template/charge_template/"+str(
                payload["data"]["template"])+"/time_charging/plans/"+str(new_id), time_charging_plan_default)
            self.max_id_charge_template_time_charging_plan = new_id
            pub.pub(
                "openWB/set/command/max_id/charge_template_time_charging_plan", new_id)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(
                payload, connection_id, "Es ist ein interner Fehler aufgetreten: "+traceback.format_exc())

    def removeChargeTemplateTimeChargingPlan(self, connection_id: str, payload: dict) -> None:
        """ löscht einen Zeitladen-Plan.
        """
        try:
            if self.max_id_charge_template_time_charging_plan >= payload["data"]["plan"]:
                log.MainLogger().info("Zeitladen-Template mit ID " +
                                      str(payload["data"]["plan"])+" zu Template "+str(payload["data"]["template"])+" geloescht.")
                pub.pub("openWB/vehicle/template/charge_template/"+str(
                    payload["data"]["template"])+"/time_charging/plans/"+str(payload["data"]["plan"]), "")
            else:
                self.__pub_error(
                    payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(
                payload, connection_id, "Es ist ein interner Fehler aufgetreten: "+traceback.format_exc())

    def addComponent(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem eine neue Komponente erstellt werden soll.
        """
        try:
            new_id = self.max_id_component + 1
            log.MainLogger().info("Neue Komponente vom Typ" +
                                  str(payload["data"]["type"])+" mit ID "+str(new_id)+" hinzugefuegt.")
            component = importlib.import_module(
                ".modules."+payload["data"]["deviceType"]+"."+payload["data"]["type"], "packages")
            component_default = component.get_default()
            component_default["id"] = new_id
            if payload["data"]["type"] == "counter":
                data.data.counter_data["all"].hierarchy_add_item_below(
                    "counter"+str(new_id), data.data.counter_data["all"].data["get"]["hierarchy"][0]["id"])
            pub.pub("openWB/set/system/device/"+str(
                payload["data"]["deviceId"])+"/component/"+str(new_id)+"/config", component_default)
            self.max_id_component = self.max_id_component + 1
            pub.pub("openWB/set/command/max_id/component",
                    self.max_id_component)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(
                payload, connection_id, "Es ist ein interner Fehler aufgetreten: "+traceback.format_exc())

    def removeComponent(self, connection_id: str, payload: dict) -> None:
        """ löscht eine Komponente.
        """
        try:
            if self.max_id_component >= payload["data"]["id"]:
                if payload["data"]["type"] == "counter":
                    data.data.counter_data["all"].hierarchy_remove_item(
                        "counter"+str(payload["data"]["id"]))
                log.MainLogger().info("Komponente mit ID " +
                                      str(payload["data"]["id"])+" geloescht.")
                ProcessBrokerBranch("system/device/"+str(
                    payload["data"]["deviceId"])+"/component/"+str(payload["data"]["id"])).remove_topics()
            else:
                self.__pub_error(
                    payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(
                payload, connection_id, "Es ist ein interner Fehler aufgetreten: "+traceback.format_exc())

    def addEvTemplate(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neues EV-Template erstellt werden soll.
        """
        try:
            new_id = self.max_id_ev_template + 1
            log.MainLogger().info("Neues EV-Template mit ID "+str(new_id)+" hinzugefuegt.")
            ev_template_default = ev.get_ev_template_default()
            pub.pub("openWB/set/vehicle/template/ev_template/" +
                    str(new_id), ev_template_default)
            self.max_id_ev_template = new_id
            pub.pub("openWB/set/command/max_id/ev_template", new_id)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(
                payload, connection_id, "Es ist ein interner Fehler aufgetreten: "+traceback.format_exc())

    def removeEvTemplate(self, connection_id: str, payload: dict) -> None:
        """ löscht ein EV-Template.
        """
        try:
            if self.max_id_ev_template >= payload["data"]["id"]:
                log.MainLogger().info("EV-Template mit ID " +
                                      str(payload["data"]["id"])+" geloescht.")
                pub.pub("openWB/vehicle/template/ev_template/" +
                        str(payload["data"]["id"]), "")
            else:
                self.__pub_error(
                    payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(
                payload, connection_id, "Es ist ein interner Fehler aufgetreten: "+traceback.format_exc())

    def addVehicle(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neues Vehicle erstellt werden soll.
        """
        try:
            new_id = self.max_id_vehicle + 1
            log.MainLogger().info("Neues EV mit ID "+str(new_id)+" hinzugefuegt.")
            vehicle_default = ev.get_vehicle_default()
            for default in vehicle_default:
                pub.pub("openWB/set/vehicle/"+str(new_id)+"/" +
                        str(default), vehicle_default[default])
            self.max_id_vehicle = self.max_id_vehicle + 1
            pub.pub("openWB/set/command/max_id/vehicle", self.max_id_vehicle)
            # Default-Mäßig werden die Templates 0 zugewiesen, wenn diese noch nicht existieren -> anlegen
            if self.max_id_charge_template == -1:
                self.addChargeTemplate("addVehicle", {})
            if self.max_id_ev_template == -1:
                self.addEvTemplate("addVehicle", {})
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(
                payload, connection_id, "Es ist ein interner Fehler aufgetreten: "+traceback.format_exc())

    def removeVehicle(self, connection_id: str, payload: dict) -> None:
        """ löscht ein Vehicle.
        """
        try:
            if self.max_id_vehicle >= payload["data"]["id"]:
                log.MainLogger().info(
                    "EV mit ID "+str(payload["data"]["id"])+" geloescht.")
                pub.pub("openWB/vehicle/"+str(payload["data"]["id"]), "")
                ProcessBrokerBranch(
                    "vehicle"+str(payload["data"]["id"])).remove_topics()
            else:
                self.__pub_error(
                    payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(
                payload, connection_id, "Es ist ein interner Fehler aufgetreten: "+traceback.format_exc())


class ProcessBrokerBranch:
    def __init__(self, topic_str: str) -> None:
        self.topic_str = topic_str

    def remove_topics(self):
        """ löscht einen Topic-Zweig auf dem Broker. Payload "" löscht nur ein einzelnes Topic.
        """
        try:
            self.__connect_to_broker(self.__on_message_rm)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def get_max_id(self):
        try:
            self.max_id = -1
            self.search_str = "openWB/" + self.topic_str.replace("+", "[0-9]+")
            self.__connect_to_broker(self.__on_message_max_id)
            return self.max_id
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def __connect_to_broker(self, on_message):
        """ abonniert alle Topics.
        """
        try:
            mqtt_broker_ip = "localhost"
            client = mqtt.Client(
                "openWB-proccesBrokerBranch-" + str(self.__getserial()))

            client.on_connect = self.__on_connect
            client.on_message = on_message

            client.connect(mqtt_broker_ip, 1886)
            client.loop_start()
            time.sleep(0.5)
            client.loop_stop()

        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def __on_connect(self, client, userdata, flags, rc):
        """ connect to broker and subscribe to set topics
        """
        try:
            client.subscribe("openWB/"+self.topic_str+"/#", 2)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def __on_message_rm(self, client, userdata, msg):
        """ wartet auf eingehende Topics.
        """
        try:
            if str(msg.payload.decode("utf-8")) != '':
                log.MainLogger().debug("Geloeschtes Topic: "+str(msg.topic))
                pub.pub(msg.topic, "")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def __on_message_max_id(self, client, userdata, msg):
        try:
            topic_found = re.search(
                '^('+self.search_str+'/*).*$', msg.topic).group(1)
            topic_rest = msg.topic.replace(topic_found, "")
            current_id_regex = re.search('^([0-9]+)/*.*$', topic_rest)
            if current_id_regex is not None:
                current_id = int(current_id_regex.group(1))
                self.max_id = max(current_id, self.max_id)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def __getserial(self):
        """ Extract serial from cpuinfo file
        """
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line[0:6] == 'Serial':
                        return line[10:26]
                return "0000000000000000"
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
