"""verarbeitet Befehl vom Broker
"""

import json
import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as subscribe
import re
import time

from . import defaults
from . import log
from . import pub
from .system import exit_after


class Command():
    """
    """
    def __init__(self):
        try:
            self.max_id_charge_template = None
            self.max_id_charge_template_scheduled_plan = None
            self.max_id_charge_template_time_charging_plan = None
            self.max_id_component = None
            self.max_id_device = None
            self.max_id_ev_template = None
            self.max_id_vehicle = None
            self.__get_max_id("charge_template")
            self.__get_max_id("charge_template_scheduled_plan")
            self.__get_max_id("charge_template_time_charging_plan")
            self.__get_max_id("component")
            self.__get_max_id("device")
            self.__get_max_id("ev_template")
            self.__get_max_id("vehicle")
            self.__chech_max_id_initalisation(self.max_id_charge_template, "charge_template", "Ladevorlage")
            self.__chech_max_id_initalisation(self.max_id_charge_template_scheduled_plan, "charge_template_scheduled_plan", "Ladevorlage - Zielladen-Plan")
            self.__chech_max_id_initalisation(self.max_id_charge_template_time_charging_plan, "charge_template_time_charging_plan", "Ladevorlage - Zeit-Plan")
            self.__chech_max_id_initalisation(self.max_id_component, "component", "Komponenten")
            self.__chech_max_id_initalisation(self.max_id_device, "device", "Devices")
            self.__chech_max_id_initalisation(self.max_id_ev_template, "ev_template", "EV-Vorlage")
            self.__chech_max_id_initalisation(self.max_id_vehicle, "vehicle", "EVs")
        except:
            log.MainLogger().exception("Fehler im Command-Modul")

    @exit_after(1)
    def __get_max_id(self, topic: str)-> None:
        """ ermittelt die maximale ID vom Broker """
        try:
            msg = subscribe.simple("openWB/command/max_id/"+topic, port=1886)
            self.__process_max_id_topic(msg, no_log = True)
        except:
            log.MainLogger().exception("Fehler im Command-Modul")

    def __chech_max_id_initalisation(self, var: int, topic: str, name: str) -> None:
        """ Wenn keine ID vom Broker empfangen wurde, wird die maximale ID mit -1 initalisiert. (Dies sollte nur beim initialen Boot vorkommen.)"""
        try:
            if var == None:
                var = -1
                pub.pub("openWB/set/command/max_id/"+topic, var)
                log.MainLogger().warning("Maximale ID für "+name+" wurde mit -1 initialisiert.")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def sub_commands(self):
        """ abonniert alle Topics.
        """
        try:
            mqtt_broker_ip = "localhost"
            client = mqtt.Client("openWB-command-" + self.getserial())

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
                    # Methoden-Name = Befehl
                    try:
                        func = getattr(self, payload["command"])
                        if "add" in payload["command"]:
                            func(payload)
                        else:
                            connection_id = self.get_connection_id(msg.topic)
                            func(connection_id, payload)
                        pub.pub(msg.topic, "")
                    except:
                        log.MainLogger().error("Zu dem Befehl wurde keine Methode gefunden.")
                elif "max_id" in msg.topic:
                    self.__process_max_id_topic(msg)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def get_connection_id(self, topic: str) -> str:
        """extrahiert die Connection ID aus einem Topic (Zahl zwischen zwei // oder am Stringende)

         Parameters
        ----------
        topic : str
            Topic, aus dem der Index extrahiert wird
        """
        try:
            connection_id = re.search('(?!/)([0-9]*)(?=/|$)', topic)
            return connection_id.group()
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def __process_max_id_topic(self, msg, no_log: bool = False) -> None:
        try:
            payload = json.loads(str(msg.payload.decode("utf-8")))
            var = re.search("/([a-z,A-Z,0-9,_]+)(?!.*/)", msg.topic).group(1)
            # Der Variablen-Name für die maximale ID setzt sich aus "max_id_" und dem Topic-Namen nach dem letzten / zusammen.
            setattr(self, "max_id_"+var, payload) 
            if no_log == False:
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
            pub.pub("openWB/set/command/"+str(connection_id)+"/error", error_payload)
            log.MainLogger().error("Befehl konnte nicht ausgefuehrt werden: "+str(error_payload))
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def addDevice(self, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neues Device erstellt werden soll.
        """
        try:
            new_id = self.max_id_device + 1
            self.max_id_device = self.max_id_device + 1
            pub.pub("openWB/set/command/max_id/device", self.max_id_device)
            log.MainLogger().info("Neues Device vom Typ"+str(payload["data"]["type"])+" mit ID "+str(new_id)+" hinzugefuegt.")
            device_default = defaults.get_device_defaults(payload["data"]["type"])
            device_default["id"] = new_id
            pub.pub("openWB/set/system/device/"+str(new_id)+"/config", device_default)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def removeDevice(self, connection_id: str, payload: dict) -> None:
        """ löscht ein Device.
        """
        try:
            if self.max_id_device >= payload["data"]["id"]:
                log.MainLogger().info("Device mit ID "+str(payload["data"]["id"])+" geloescht.")
                RemoveTopicsRecursively("system/device/"+str(payload["data"]["id"]))
            else:
                self.__pub_error(payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def addChargeTemplate(self, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neues Vehicle erstellt werden soll.
        """
        try:
            new_id = self.max_id_charge_template + 1
            self.max_id_charge_template = new_id
            pub.pub("openWB/set/command/max_id/charge_template", new_id)
            log.MainLogger().info("Neues Lade-Template mit ID "+str(new_id)+" hinzugefuegt.")
            charge_template_default = defaults.get_charge_template_defaults()
            pub.pub("openWB/set/vehicle/template/charge_template/"+str(new_id), charge_template_default)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def removeChargeTemplate(self, connection_id: str, payload: dict) -> None:
        """ löscht ein Vehicle.
        """
        try:
            if self.max_id_charge_template >= payload["data"]["id"]:
                log.MainLogger().info("Lade-Template mit ID "+str(payload["data"]["id"])+" geloescht.")
                pub.pub("openWB/vehicle/template/charge_template/"+str(payload["data"]["id"]), "")
            else:
                self.__pub_error(payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def addChargeTemplateSchedulePlan(self, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neues Vehicle erstellt werden soll.
        """
        try:
            new_id = self.max_id_charge_template_scheduled_plan + 1
            self.max_id_charge_template_scheduled_plan = new_id
            pub.pub("openWB/set/command/max_id/charge_template_scheduled_plan", new_id)
            log.MainLogger().info("Neues Zielladen-Template mit ID "+str(new_id)+" zu Template "+str(payload["data"]["template"])+" hinzugefuegt.")
            charge_template_default = defaults.get_charge_template_scheduled_plan_defaults()
            pub.pub("openWB/set/vehicle/template/charge_template/"+str(payload["data"]["template"])+"/chargemode/scheduled_charging/plans/"+str(new_id), charge_template_default)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def removeChargeTemplateSchedulePlan(self, connection_id: str, payload: dict) -> None:
        """ löscht ein Vehicle.
        """
        try:
            if self.max_id_charge_template_scheduled_plan >= payload["data"]["plan"]:
                log.MainLogger().info("Zielladen-Template mit ID "+str(payload["data"]["plan"])+" zu Template "+str(payload["data"]["template"])+" geloescht.")
                pub.pub("openWB/vehicle/template/charge_template/"+str(payload["data"]["template"])+"/chargemode/scheduled_charging/plans/"+str(payload["data"]["plan"]), "")
            else:
                self.__pub_error(payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def addChargeTemplateTimeChargingPlan(self, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neues Vehicle erstellt werden soll.
        """
        try:
            new_id = self.max_id_charge_template_time_charging_plan + 1
            self.max_id_charge_template_time_charging_plan = new_id
            pub.pub("openWB/set/command/max_id/charge_template_time_charging_plan", new_id)
            log.MainLogger().info("Neues Zeitladen-Template mit ID "+str(new_id)+" zu Template "+str(payload["data"]["template"])+" hinzugefuegt.")
            time_charging_plan_default = defaults.get_charge_template_time_charging_plan_defaults()
            pub.pub("openWB/set/vehicle/template/charge_template/"+str(payload["data"]["template"])+"/time_charging/plans/"+str(new_id), time_charging_plan_default)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def removeChargeTemplateTimeChargingPlan(self, connection_id: str, payload: dict) -> None:
        """ löscht ein Vehicle.
        """
        try:
            if self.max_id_charge_template_time_charging_plan >= payload["data"]["plan"]:
                log.MainLogger().info("Zeitladen-Template mit ID "+str(payload["data"]["plan"])+" zu Template "+str(payload["data"]["template"])+" geloescht.")
                pub.pub("openWB/vehicle/template/charge_template/"+str(payload["data"]["template"])+"/time_charging/plans/"+str(payload["data"]["plan"]), "")
            else:
                self.__pub_error(payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def addComponent(self, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neues Device erstellt werden soll.
        """
        try:
            new_id = self.max_id_component + 1
            self.max_id_component = self.max_id_component + 1
            pub.pub("openWB/set/command/max_id/component", self.max_id_component)
            log.MainLogger().info("Neue Komponente vom Typ"+str(payload["data"]["type"])+" mit ID "+str(new_id)+" hinzugefuegt.")
            component_default = defaults.get_component_defaults(payload["data"]["deviceType"], payload["data"]["type"])
            component_default["id"] = new_id
            pub.pub("openWB/set/system/device/"+str(payload["data"]["deviceId"])+"/component/"+str(new_id)+"/config", component_default)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def removeComponent(self, connection_id: str, payload: dict) -> None:
        """ löscht ein Device.
        """
        try:
            if self.max_id_component >= payload["data"]["id"]:
                log.MainLogger().info("Komponente mit ID "+str(payload["data"]["id"])+" geloescht.")
                RemoveTopicsRecursively("system/device/"+str(payload["data"]["deviceId"])+"/component/"+str(payload["data"]["id"]))
            else:
                self.__pub_error(payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def addEvTemplate(self, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neues Vehicle erstellt werden soll.
        """
        try:
            new_id = self.max_id_ev_template + 1
            self.max_id_ev_template = new_id
            pub.pub("openWB/set/command/max_id/ev_template", new_id)
            log.MainLogger().info("Neues EV-Template mit ID "+str(new_id)+" hinzugefuegt.")
            ev_template_default = defaults.get_ev_template_defaults()
            pub.pub("openWB/set/vehicle/template/ev_template/"+str(new_id), ev_template_default)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def removeEvTemplate(self, connection_id: str, payload: dict) -> None:
        """ löscht ein Vehicle.
        """
        try:
            if self.max_id_ev_template >= payload["data"]["id"]:
                log.MainLogger().info("EV-Template mit ID "+str(payload["data"]["id"])+" geloescht.")
                pub.pub("openWB/vehicle/template/ev_template/"+str(payload["data"]["id"]), "")
            else:
                self.__pub_error(payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def addVehicle(self, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neues Vehicle erstellt werden soll.
        """
        try:
            new_id = self.max_id_vehicle + 1
            self.max_id_vehicle = self.max_id_vehicle + 1
            pub.pub("openWB/set/command/max_id/vehicle", self.max_id_vehicle)
            log.MainLogger().info("Neues EV mit ID "+str(new_id)+" hinzugefuegt.")
            vehicle_default = defaults.get_vehicle_defaults()
            for default in vehicle_default:
                pub.pub("openWB/set/vehicle/"+str(new_id)+"/"+str(default), vehicle_default[default])
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def removeVehicle(self, connection_id: str, payload: dict) -> None:
        """ löscht ein Vehicle.
        """
        try:
            if self.max_id_vehicle >= payload["data"]["id"]:
                log.MainLogger().info("EV mit ID "+str(payload["data"]["id"])+" geloescht.")
                pub.pub("openWB/vehicle/"+str(payload["data"]["id"]), "")
                RemoveTopicsRecursively("vehicle"+payload["data"]["id"])
            else:
                self.__pub_error(payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

class RemoveTopicsRecursively:
    """ löscht mehrere Topics in einem Ordner. Payload "" löscht nur ein einzelnes Topic.
    """
    def __init__(self, topic_str: str) -> None:
        self.topic_str = topic_str
        self.remove_topics()

    def remove_topics(self):
        """ abonniert alle Topics.
        """
        try:
            mqtt_broker_ip = "localhost"
            client = mqtt.Client("openWB-remove-" + self.getserial())

            client.on_connect = self.on_connect_rm
            client.on_message = self.on_message_rm

            client.connect(mqtt_broker_ip, 1886)
            client.loop_start()
            time.sleep(0.5)
            client.loop_stop()
            
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def on_connect_rm(self, client, userdata, flags, rc):
        """ connect to broker and subscribe to set topics
        """
        try:
            client.subscribe("openWB/"+self.topic_str+"/#", 2)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def on_message_rm(self, client, userdata, msg):
        """ wartet auf eingehende Topics.
        """
        try:
            if str(msg.payload.decode("utf-8")) != '':
                log.MainLogger().debug("Geloeschtes Topic: "+str(msg.topic))
                pub.pub(msg.topic, "")
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