"""verarbeitet Befehl vom Broker
"""

import importlib
import json
import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as subscribe
import re
import time

from . import log
from . import pub
from ..algorithm import chargepoint
from ..algorithm import ev
from .system import exit_after


class Command():
    """
    """
    def __init__(self):
        try:
            self.max_id_charge_template = None
            self.max_id_charge_template_scheduled_plan = None
            self.max_id_charge_template_time_charging_plan = None
            self.max_id_chargepoint = None
            self.max_id_chargepoint_template = None
            self.max_id_component = None
            self.max_id_device = None
            self.max_id_ev_template = None
            self.max_id_vehicle = None
            self.__get_max_id("charge_template")
            self.__get_max_id("charge_template_scheduled_plan")
            self.__get_max_id("charge_template_time_charging_plan")
            self.__get_max_id("chargepoint")
            self.__get_max_id("chargepoint_template")
            self.__get_max_id("component")
            self.__get_max_id("device")
            self.__get_max_id("ev_template")
            self.__get_max_id("vehicle")
            self.__chech_max_id_initalisation(self.max_id_charge_template, "charge_template", "Ladevorlage")
            self.__chech_max_id_initalisation(self.max_id_charge_template_scheduled_plan, "charge_template_scheduled_plan", "Ladevorlage - Zielladen-Plan")
            self.__chech_max_id_initalisation(self.max_id_charge_template_time_charging_plan, "charge_template_time_charging_plan", "Ladevorlage - Zeit-Plan")
            self.__chech_max_id_initalisation(self.max_id_chargepoint, "chargepoint", "Ladepunkt")
            self.__chech_max_id_initalisation(self.max_id_chargepoint_template, "chargepoint_template", "Ladepunkt-Vorlage")
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
                    connection_id = self.get_connection_id(msg.topic)
                    # Methoden-Name = Befehl
                    try:
                        func = getattr(self, payload["command"])
                        func(connection_id, payload)
                    except:
                        log.MainLogger().error("Zu dem Befehl wurde keine Methode gefunden.")
                        self.__pub_error(payload, connection_id, "Zu dem Befehl wurde keine Methode gefunden.")
                    pub.pub(msg.topic, "")
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
            pub.pub("openWB/set/command/"+str(connection_id)+"/error", str(error_payload))
            log.MainLogger().error("Befehl konnte nicht ausgefuehrt werden: "+str(error_payload))
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def addDevice(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neues Device erstellt werden soll.
        """
        try:
            new_id = self.max_id_device + 1
            log.MainLogger().info("Neues Device vom Typ"+str(payload["data"]["type"])+" mit ID "+str(new_id)+" hinzugefuegt.")
            dev = importlib.import_module(".modules."+payload["data"]["type"]+".device", "packages")
            device_default = dev.get_default()
            device_default["id"] = new_id
            pub.pub("openWB/set/system/device/"+str(new_id)+"/config", device_default)
            self.max_id_device = self.max_id_device + 1
            pub.pub("openWB/set/command/max_id/device", self.max_id_device)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(payload, connection_id, "Es ist ein interner Fehler aufgetreten.")

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
            self.__pub_error(payload, connection_id, "Es ist ein interner Fehler aufgetreten.")

    def addChargepoint(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neuer Chargepoint erstellt werden soll.
        """
        try:
            new_id = self.max_id_chargepoint + 1
            log.MainLogger().info("Neuer Ladepunkt vom Typ"+str(payload["data"]["type"])+" mit ID "+str(new_id)+" hinzugefuegt.")
            chargepoint_default = chargepoint.get_chargepoint_default()
            chargepoint_default["id"] = new_id
            pub.pub("openWB/set/chargepoint/"+str(new_id)+"/config", chargepoint_default)
            self.max_id_chargepoint = self.max_id_chargepoint + 1
            pub.pub("openWB/set/command/max_id/chargepoint", self.max_id_chargepoint)
            if self.max_id_chargepoint_template == -1:
                self.addChargepointTemplate("addChargepoint", {})
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(payload, connection_id, "Es ist ein interner Fehler aufgetreten.")

    def removeChargepoint(self, connection_id: str, payload: dict) -> None:
        """ löscht ein Chargepoint.
        """
        try:
            if self.max_id_chargepoint >= payload["data"]["id"]:
                log.MainLogger().info("Ladepunkt mit ID "+str(payload["data"]["id"])+" geloescht.")
                RemoveTopicsRecursively("chargepoint/"+str(payload["data"]["id"]))
            else:
                self.__pub_error(payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(payload, connection_id, "Es ist ein interner Fehler aufgetreten.")

    def addChargepointTemplate(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem eine neue Ladepunkt-Vorlage erstellt werden soll.
        """
        try:
            new_id = self.max_id_chargepoint_template + 1
            log.MainLogger().info("Neue Ladepunkt-Vorlage vom Typ"+str(payload["data"]["type"])+" mit ID "+str(new_id)+" hinzugefuegt.")
            default = chargepoint.get_chargepoint_template_default()
            default["id"] = new_id
            for d in default:
                if isinstance(d, dict):
                    for d2 in d:
                        pub.pub("openWB/set/chargepoint/template/"+str(new_id)+"/"+str(d)+"/"+str(d2), default[d][d2])
                else:
                    pub.pub("openWB/set/chargepoint/template/"+str(new_id)+"/"+str(d), default[d])
            self.max_id_chargepoint_template = self.max_id_chargepoint_template + 1
            pub.pub("openWB/set/command/max_id/chargepoint_template", self.max_id_chargepoint_template)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(payload, connection_id, "Es ist ein interner Fehler aufgetreten.")

    def removeChargepointTemplate(self, connection_id: str, payload: dict) -> None:
        """ löscht eine ladepunkt-Vorlage.
        """
        try:
            if self.max_id_chargepoint_template >= payload["data"]["id"]:
                log.MainLogger().info("Ladepunkt-Vorlage mit ID "+str(payload["data"]["id"])+" geloescht.")
                RemoveTopicsRecursively("chargepoint/template/"+str(payload["data"]["id"]))
            else:
                self.__pub_error(payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(payload, connection_id, "Es ist ein interner Fehler aufgetreten.")

    def addChargeTemplate(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem eine neue Lade-Vorlage erstellt werden soll.
        """
        try:
            new_id = self.max_id_charge_template + 1
            log.MainLogger().info("Neues Lade-Template mit ID "+str(new_id)+" hinzugefuegt.")
            charge_template_default = ev.get_charge_template_default()
            pub.pub("openWB/set/vehicle/template/charge_template/"+str(new_id), charge_template_default)
            self.max_id_charge_template = new_id
            pub.pub("openWB/set/command/max_id/charge_template", new_id)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(payload, connection_id, "Es ist ein interner Fehler aufgetreten.")

    def removeChargeTemplate(self, connection_id: str, payload: dict) -> None:
        """ löscht eine Lade-Vorlage.
        """
        try:
            if self.max_id_charge_template >= payload["data"]["id"]:
                log.MainLogger().info("Lade-Template mit ID "+str(payload["data"]["id"])+" geloescht.")
                pub.pub("openWB/vehicle/template/charge_template/"+str(payload["data"]["id"]), "")
            else:
                self.__pub_error(payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(payload, connection_id, "Es ist ein interner Fehler aufgetreten.")

    def addChargeTemplateSchedulePlan(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neuer Zielladen-Plan erstellt werden soll.
        """
        try:
            new_id = self.max_id_charge_template_scheduled_plan + 1
            log.MainLogger().info("Neues Zielladen-Template mit ID "+str(new_id)+" zu Template "+str(payload["data"]["template"])+" hinzugefuegt.")
            charge_template_default = ev.get_charge_template_scheduled_plan_default()
            pub.pub("openWB/set/vehicle/template/charge_template/"+str(payload["data"]["template"])+"/chargemode/scheduled_charging/plans/"+str(new_id), charge_template_default)
            self.max_id_charge_template_scheduled_plan = new_id
            pub.pub("openWB/set/command/max_id/charge_template_scheduled_plan", new_id)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(payload, connection_id, "Es ist ein interner Fehler aufgetreten.")

    def removeChargeTemplateSchedulePlan(self, connection_id: str, payload: dict) -> None:
        """ löscht einen Zielladen-Plan.
        """
        try:
            if self.max_id_charge_template_scheduled_plan >= payload["data"]["plan"]:
                log.MainLogger().info("Zielladen-Template mit ID "+str(payload["data"]["plan"])+" zu Template "+str(payload["data"]["template"])+" geloescht.")
                pub.pub("openWB/vehicle/template/charge_template/"+str(payload["data"]["template"])+"/chargemode/scheduled_charging/plans/"+str(payload["data"]["plan"]), "")
            else:
                self.__pub_error(payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(payload, connection_id, "Es ist ein interner Fehler aufgetreten.")

    def addChargeTemplateTimeChargingPlan(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neuer Zeitladen-Plan erstellt werden soll.
        """
        try:
            new_id = self.max_id_charge_template_time_charging_plan + 1
            log.MainLogger().info("Neues Zeitladen-Template mit ID "+str(new_id)+" zu Template "+str(payload["data"]["template"])+" hinzugefuegt.")
            time_charging_plan_default = ev.get_charge_template_time_charging_plan_default()
            pub.pub("openWB/set/vehicle/template/charge_template/"+str(payload["data"]["template"])+"/time_charging/plans/"+str(new_id), time_charging_plan_default)
            self.max_id_charge_template_time_charging_plan = new_id
            pub.pub("openWB/set/command/max_id/charge_template_time_charging_plan", new_id)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(payload, connection_id, "Es ist ein interner Fehler aufgetreten.")

    def removeChargeTemplateTimeChargingPlan(self, connection_id: str, payload: dict) -> None:
        """ löscht einen Zeitladen-Plan.
        """
        try:
            if self.max_id_charge_template_time_charging_plan >= payload["data"]["plan"]:
                log.MainLogger().info("Zeitladen-Template mit ID "+str(payload["data"]["plan"])+" zu Template "+str(payload["data"]["template"])+" geloescht.")
                pub.pub("openWB/vehicle/template/charge_template/"+str(payload["data"]["template"])+"/time_charging/plans/"+str(payload["data"]["plan"]), "")
            else:
                self.__pub_error(payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(payload, connection_id, "Es ist ein interner Fehler aufgetreten.")

    def addComponent(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem eine neue Komponente erstellt werden soll.
        """
        try:
            new_id = self.max_id_component + 1
            log.MainLogger().info("Neue Komponente vom Typ"+str(payload["data"]["type"])+" mit ID "+str(new_id)+" hinzugefuegt.")
            component = importlib.import_module(".modules."+payload["data"]["deviceType"]+"."+payload["data"]["type"], "packages")
            component_default = component.get_default()
            component_default["id"] = new_id
            pub.pub("openWB/set/system/device/"+str(payload["data"]["deviceId"])+"/component/"+str(new_id)+"/config", component_default)
            self.max_id_component = self.max_id_component + 1
            pub.pub("openWB/set/command/max_id/component", self.max_id_component)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(payload, connection_id, "Es ist ein interner Fehler aufgetreten.")

    def removeComponent(self, connection_id: str, payload: dict) -> None:
        """ löscht eine Komponente.
        """
        try:
            if self.max_id_component >= payload["data"]["id"]:
                log.MainLogger().info("Komponente mit ID "+str(payload["data"]["id"])+" geloescht.")
                RemoveTopicsRecursively("system/device/"+str(payload["data"]["deviceId"])+"/component/"+str(payload["data"]["id"]))
            else:
                self.__pub_error(payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(payload, connection_id, "Es ist ein interner Fehler aufgetreten.")

    def addEvTemplate(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neues EV-Template erstellt werden soll.
        """
        try:
            new_id = self.max_id_ev_template + 1
            log.MainLogger().info("Neues EV-Template mit ID "+str(new_id)+" hinzugefuegt.")
            ev_template_default = ev.get_ev_template_default()
            pub.pub("openWB/set/vehicle/template/ev_template/"+str(new_id), ev_template_default)
            self.max_id_ev_template = new_id
            pub.pub("openWB/set/command/max_id/ev_template", new_id)
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(payload, connection_id, "Es ist ein interner Fehler aufgetreten.")

    def removeEvTemplate(self, connection_id: str, payload: dict) -> None:
        """ löscht ein EV-Template.
        """
        try:
            if self.max_id_ev_template >= payload["data"]["id"]:
                log.MainLogger().info("EV-Template mit ID "+str(payload["data"]["id"])+" geloescht.")
                pub.pub("openWB/vehicle/template/ev_template/"+str(payload["data"]["id"]), "")
            else:
                self.__pub_error(payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(payload, connection_id, "Es ist ein interner Fehler aufgetreten.")

    def addVehicle(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neues Vehicle erstellt werden soll.
        """
        try:
            new_id = self.max_id_vehicle + 1
            log.MainLogger().info("Neues EV mit ID "+str(new_id)+" hinzugefuegt.")
            vehicle_default = ev.get_vehicle_default()
            for default in vehicle_default:
                pub.pub("openWB/set/vehicle/"+str(new_id)+"/"+str(default), vehicle_default[default])
            self.max_id_vehicle = self.max_id_vehicle + 1
            pub.pub("openWB/set/command/max_id/vehicle", self.max_id_vehicle)
            # Default-Mäßig werden die Templates 0 zugewiesen, wenn diese noch nicht existieren -> anlegen
            if self.max_id_charge_template == -1:
                self.addChargeTemplate("addVehicle", {})
            if self.max_id_ev_template == -1:
                self.addEvTemplate("addVehicle", {})
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")
            self.__pub_error(payload, connection_id, "Es ist ein interner Fehler aufgetreten.")

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
            self.__pub_error(payload, connection_id, "Es ist ein interner Fehler aufgetreten.")

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