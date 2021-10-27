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
            self.max_id_device = None
            self.max_id_component = None
            self.max_id_vehicle = None
            self.__get_max_id("device")
            self.__get_max_id("component")
            self.__get_max_id("vehicle")
            self.__chech_max_id_initalisation(self.max_id_device, "device", "Devices")
            self.__chech_max_id_initalisation(self.max_id_component, "component", "Komponenten")
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
                    if payload["command"] == "addDevice":
                        self.__add_device(msg.topic, payload)
                    elif payload["command"] == "removeDevice":
                        self.__remove_device(msg.topic, payload)
                    elif payload["command"] == "addComponent":
                        self.__add_component(msg.topic, payload)
                    elif payload["command"] == "removeComponent":
                        self.__remove_component(msg.topic, payload)
                    elif payload["command"] == "addVehicle":
                        self.__add_vehicle(msg.topic)
                    elif payload["command"] == "removeVehicle":
                        self.__remove_vehicle(msg.topic, payload)
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
            if "openWB/command/max_id/device" in msg.topic:
                self.max_id_device = json.loads(str(msg.payload.decode("utf-8")))
                if no_log == False:
                    log.MainLogger().debug("Max ID Device "+str(self.max_id_device))
            elif "openWB/command/max_id/component" in msg.topic:
                self.max_id_component = json.loads(str(msg.payload.decode("utf-8")))
                if no_log == False:
                    log.MainLogger().debug("Max ID Komponente "+str(self.max_id_component))
            elif "openWB/command/max_id/vehicle" in msg.topic:
                self.max_id_vehicle = json.loads(str(msg.payload.decode("utf-8")))
                if no_log == False:
                    log.MainLogger().debug("Max ID EV "+str(self.max_id_component))
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

    def __add_device(self, topic: str, payload: dict) -> None:
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
            pub.pub(topic, "")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def __remove_device(self, topic: str, payload: dict) -> None:
        """ löscht ein Device.
        """
        try:
            connection_id = self.get_connection_id(topic)
            if self.max_id_device >= payload["data"]["id"]:
                log.MainLogger().info("Device mit ID "+str(payload["data"]["id"])+" geloescht.")
                RemoveTopicsRecursively("system/device/"+str(payload["data"]["id"]))
            else:
                self.__pub_error(payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
            pub.pub(topic, "")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def __add_component(self, topic: str, payload: dict) -> None:
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
            pub.pub(topic, "")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def __remove_component(self, topic: str, payload: dict) -> None:
        """ löscht ein Device.
        """
        try:
            connection_id = self.get_connection_id(topic)
            if self.max_id_component >= payload["data"]["id"]:
                log.MainLogger().info("Komponente mit ID "+str(payload["data"]["id"])+" geloescht.")
                RemoveTopicsRecursively("system/device/"+str(payload["data"]["deviceId"])+"/component/"+str(payload["data"]["id"]))
            else:
                self.__pub_error(payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
            pub.pub(topic, "")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def __add_vehicle(self, topic: str) -> None:
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
            pub.pub(topic, "")
        except Exception as e:
            log.MainLogger().exception("Fehler im Command-Modul")

    def __remove_vehicle(self, topic: str, payload: dict) -> None:
        """ löscht ein Vehicle.
        """
        try:
            connection_id = self.get_connection_id(topic)
            if self.max_id_vehicle >= payload["data"]["id"]:
                log.MainLogger().info("EV mit ID "+str(payload["data"]["id"])+" geloescht.")
                pub.pub("openWB/vehicle/"+str(payload["data"]["id"]), "")
                RemoveTopicsRecursively("vehicle"+payload["data"]["id"])
            else:
                self.__pub_error(payload, connection_id, "Die ID ist groesser als die maximal vergebene ID.")
            pub.pub(topic, "")
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