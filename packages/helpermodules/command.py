"""verarbeitet Befehl vom Broker
"""

import importlib
import json
import subprocess
import paho.mqtt.client as mqtt
import re
import time
import traceback
from pathlib import Path

from helpermodules.log import MainLogger
from helpermodules import measurement_log
from helpermodules.pub import Pub
from control import bridge
from control import chargepoint
from control import data
from control import ev
from control import counter


class Command:
    """
    """

    def __init__(self):
        try:
            self.__get_max_id("autolock_plan", "chargepoint/template/+/autolock", -1)
            self.__get_max_id("mqtt_bridge", "system/mqtt/bridge", -1)
            self.__get_max_id("charge_template", "vehicle/template/charge_template", 0)
            self.__get_max_id(
                "charge_template_scheduled_plan",
                "vehicle/template/charge_template/+/chargemode/scheduled_charging/plans", -1)
            self.__get_max_id(
                "charge_template_time_charging_plan",
                "vehicle/template/charge_template/+/time_charging/plans", -1)
            self.__get_max_id("chargepoint", "chargepoint", 0)
            self.__get_max_id("chargepoint_template", "chargepoint/template", 0)
            self.__get_max_id("component", "system/device/+/component", -1)
            self.__get_max_id("device", "system/device", -1)
            self.__get_max_id("ev_template", "vehicle/template/ev_template", 0)
            self.__get_max_id("vehicle", "vehicle", 0)
        except Exception:
            MainLogger().exception("Fehler im Command-Modul")

    def __get_max_id(self, id_topic: str, topic: str, default: int) -> None:
        """ ermittelt die maximale ID vom Broker """
        try:
            max_id = ProcessBrokerBranch(topic).get_max_id(default)
            Pub().pub("openWB/set/command/max_id/"+id_topic, max_id)
        except Exception:
            MainLogger().exception("Fehler im Command-Modul")

    def sub_commands(self):
        """ abonniert alle Topics.
        """
        try:
            # kurze Pause, damit die ID vom Broker ermittelt werden können. Sonst werden noch vorher die retained
            # Topics empfangen, was zu doppelten Logmeldungen führt.
            time.sleep(1)
            mqtt_broker_ip = "localhost"
            client = mqtt.Client("openWB-command-" + str(self.getserial()))

            client.on_connect = self.on_connect
            client.on_message = self.on_message

            client.connect(mqtt_broker_ip, 1886)
            client.loop_forever()
            client.disconnect()
        except Exception:
            MainLogger().exception("Fehler im Command-Modul")

    def getserial(self):
        """ Extract serial from cpuinfo file
        """
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line[0:6] == 'Serial':
                        return line[10:26]
                return "0000000000000000"
        except Exception:
            MainLogger().exception("Fehler im Command-Modul")

    def on_connect(self, client, userdata, flags, rc):
        """ connect to broker and subscribe to set topics
        """
        try:
            client.subscribe("openWB/command/#", 2)
        except Exception:
            MainLogger().exception("Fehler im Command-Modul")

    def on_message(self, client, userdata, msg):
        """ wartet auf eingehende Topics.
        """
        try:
            if str(msg.payload.decode("utf-8")) != '':
                if "todo" in msg.topic:
                    payload = json.loads(str(msg.payload.decode("utf-8")))
                    connection_id = msg.topic.split("/")[2]
                    MainLogger().debug("Befehl: "+str(payload)+", Connection-ID: "+str(connection_id))
                    # Methoden-Name = Befehl
                    try:
                        func = getattr(self, payload["command"])
                        with ErrorHandlingContext(payload, connection_id):
                            func(connection_id, payload)
                    except Exception:
                        MainLogger().error("Zu dem Befehl wurde keine Methode gefunden.")
                        pub_error(payload, connection_id, "Zu dem Befehl wurde keine Methode gefunden.")
                    Pub().pub(msg.topic, "")
                elif "max_id" in msg.topic:
                    self.__process_max_id_topic(msg)
        except Exception:
            MainLogger().exception("Fehler im Command-Modul")

    def __process_max_id_topic(self, msg, no_log: bool = False) -> None:
        try:
            payload = json.loads(str(msg.payload.decode("utf-8")))
            result = re.search("/([a-z,A-Z,0-9,_]+)(?!.*/)", msg.topic)
            if result is not None:
                var = result.group(1)
                # Der Variablen-Name für die maximale ID setzt sich aus "max_id_" und dem Topic-Namen nach dem letzten /
                # zusammen.
                setattr(self, "max_id_"+var, payload)
                MainLogger().debug("Max ID "+var+" "+str(payload))
        except Exception:
            MainLogger().exception("Fehler im Command-Modul")

    def addDevice(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neues Device erstellt werden soll.
        """
        new_id = self.max_id_device + 1
        MainLogger().info(
            "Neues Device vom Typ "+str(payload["data"]["type"])+" mit ID "+str(new_id)+" hinzugefügt.")
        dev = importlib.import_module("."+payload["data"]["type"]+".device", "modules")
        device_default = dev.get_default_config()
        device_default["id"] = new_id
        Pub().pub("openWB/set/system/device/" +
                  str(new_id)+"/config", device_default)
        self.max_id_device = self.max_id_device + 1
        Pub().pub("openWB/set/command/max_id/device", self.max_id_device)

    def removeDevice(self, connection_id: str, payload: dict) -> None:
        """ löscht ein Device.
        """
        if self.max_id_device >= payload["data"]["id"]:
            MainLogger().info("Device mit ID " +
                              str(payload["data"]["id"])+" gelöscht.")
            ProcessBrokerBranch(
                "system/device/"+str(payload["data"]["id"])).remove_topics()
        else:
            pub_error(payload, connection_id, "Die ID ist größer als die maximal vergebene ID.")

    def addChargepoint(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neuer Chargepoint erstellt werden soll.
        """
        new_id = self.max_id_chargepoint + 1
        MainLogger().info(
            "Neuer Ladepunkt mit ID "+str(new_id)+" hinzugefügt.")
        chargepoint_default = chargepoint.get_chargepoint_default()
        chargepoint_default["id"] = new_id
        module = importlib.import_module("."+payload["data"]["type"]+".chargepoint_module", "modules")
        chargepoint_default = {**chargepoint_default, **module.get_default_config()}
        chargepoint_default["id"] = new_id
        try:
            evu_counter = data.data.counter_data["all"].get_evu_counter()
            data.data.counter_data["all"].hierarchy_add_item_below(
                "cp"+str(new_id), evu_counter)
            Pub().pub("openWB/set/chargepoint/"+str(new_id)+"/config", chargepoint_default)
            Pub().pub("openWB/set/chargepoint/"+str(new_id)+"/set/manual_lock", False)
            self.max_id_chargepoint = self.max_id_chargepoint + 1
            Pub().pub("openWB/set/command/max_id/chargepoint", self.max_id_chargepoint)
            if self.max_id_chargepoint_template == -1:
                self.addChargepointTemplate("addChargepoint", {})
            if self.max_id_vehicle == -1:
                self.addVehicle("addChargepoint", {})
        except TypeError:
            pub_error(payload, connection_id, "Bitte erst einen EVU-Zähler konfigurieren!")

    def removeChargepoint(self, connection_id: str, payload: dict) -> None:
        """ löscht ein Chargepoint.
        """
        if self.max_id_chargepoint >= payload["data"]["id"]:
            if payload["data"]["id"] > 0:
                data.data.counter_data["all"].hierarchy_remove_item(
                    "cp"+str(payload["data"]["id"]))
                MainLogger().info("Ladepunkt mit ID " +
                                  str(payload["data"]["id"])+" gelöscht.")
                ProcessBrokerBranch(
                    "chargepoint/"+str(payload["data"]["id"])).remove_topics()
            else:
                pub_error(payload, connection_id, "Ladepunkt mit ID 0 darf nicht gelöscht werden.")
        else:
            pub_error(payload, connection_id, "Die ID ist größer als die maximal vergebene ID.")

    def addChargepointTemplate(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem eine neue Ladepunkt-Vorlage erstellt werden soll.
        """
        new_id = self.max_id_chargepoint_template + 1
        MainLogger().info("Neue Ladepunkt-Vorlage mit ID "+str(new_id)+" hinzugefügt.")
        default = chargepoint.get_chargepoint_template_default()
        default["id"] = new_id
        Pub().pub("openWB/set/chargepoint/template/"+str(new_id), default)
        self.max_id_chargepoint_template = self.max_id_chargepoint_template + 1
        Pub().pub("openWB/set/command/max_id/chargepoint_template",
                  self.max_id_chargepoint_template)

    def removeChargepointTemplate(self, connection_id: str, payload: dict) -> None:
        """ löscht eine ladepunkt-Vorlage.
        """
        if self.max_id_chargepoint_template >= payload["data"]["id"]:
            if payload["data"]["id"] > 0:
                MainLogger().info("Ladepunkt-Vorlage mit ID " +
                                  str(payload["data"]["id"])+" gelöscht.")
                ProcessBrokerBranch("chargepoint/template/" +
                                    str(payload["data"]["id"])).remove_topics()
            else:
                pub_error(payload, connection_id, "Ladepunkt-Vorlage mit ID 0 darf nicht gelöscht werden.")
        else:
            pub_error(payload, connection_id, "Die ID ist größer als die maximal vergebene ID.")

    def addAutolockPlan(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neuer Zielladen-Plan erstellt werden soll.
        """
        new_id = self.max_id_autolock_plan + 1
        MainLogger().info("Neuer Autolock-Plan mit ID " + str(new_id) + " zu Template " +
                          str(payload["data"]["template"]) + " hinzugefügt.")
        default = chargepoint.get_autolock_plan_default()
        Pub().pub("openWB/set/chargepoint/template/"+str(payload["data"]
                                                         ["template"])+"/autolock/"+str(new_id), default)
        self.max_id_autolock_plan = new_id
        Pub().pub("openWB/set/command/max_id/autolock_plan", new_id)

    def removeAutolockPlan(self, connection_id: str, payload: dict) -> None:
        """ löscht einen Zielladen-Plan.
        """
        if self.max_id_autolock_plan >= payload["data"]["plan"]:
            MainLogger().info(
                "Autolock-Plan mit ID " + str(payload["data"]["plan"]) + " zu Template " +
                str(payload["data"]["template"]) + " gelöscht.")
            Pub().pub(
                "openWB/chargepoint/template/" + str(payload["data"]["template"]) + "/autolock/" +
                str(payload["data"]["plan"]),
                "")
        else:
            pub_error(payload, connection_id, "Die ID ist größer als die maximal vergebene ID.")

    def addChargeTemplate(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem eine neue Lade-Vorlage erstellt werden soll.
        """
        new_id = self.max_id_charge_template + 1
        MainLogger().info("Neues Lade-Template mit ID "+str(new_id)+" hinzugefügt.")
        charge_template_default = ev.get_charge_template_default()
        Pub().pub("openWB/set/vehicle/template/charge_template/" +
                  str(new_id), charge_template_default)
        self.max_id_charge_template = new_id
        Pub().pub("openWB/set/command/max_id/charge_template", new_id)

    def removeChargeTemplate(self, connection_id: str, payload: dict) -> None:
        """ löscht eine Lade-Vorlage.
        """
        if self.max_id_charge_template >= payload["data"]["id"]:
            if payload["data"]["id"] > 0:
                MainLogger().info("Lade-Template mit ID " +
                                  str(payload["data"]["id"])+" gelöscht.")
                Pub().pub("openWB/vehicle/template/charge_template/" +
                          str(payload["data"]["id"]), "")
            else:
                pub_error(payload, connection_id, "Ladevorlage mit ID 0 darf nicht gelöscht werden.")
        else:
            pub_error(payload, connection_id, "Die ID ist größer als die maximal vergebene ID.")

    def addChargeTemplateSchedulePlan(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neuer Zielladen-Plan erstellt werden soll.
        """
        new_id = self.max_id_charge_template_scheduled_plan + 1
        MainLogger().info("Neues Zielladen-Template mit ID " + str(new_id) + " zu Template " +
                          str(payload["data"]["template"]) + " hinzugefügt.")
        charge_template_default = ev.get_charge_template_scheduled_plan_default()
        Pub().pub(
            "openWB/set/vehicle/template/charge_template/" + str(payload["data"]["template"]) +
            "/chargemode/scheduled_charging/plans/" + str(new_id),
            charge_template_default)
        self.max_id_charge_template_scheduled_plan = new_id
        Pub().pub(
            "openWB/set/command/max_id/charge_template_scheduled_plan", new_id)

    def removeChargeTemplateSchedulePlan(self, connection_id: str, payload: dict) -> None:
        """ löscht einen Zielladen-Plan.
        """
        if self.max_id_charge_template_scheduled_plan >= payload["data"]["plan"]:
            MainLogger().info(
                "Zielladen-Template mit ID " + str(payload["data"]["plan"]) + " zu Template " +
                str(payload["data"]["template"]) + " gelöscht.")
            Pub().pub(
                "openWB/vehicle/template/charge_template/" + str(payload["data"]["template"]) +
                "/chargemode/scheduled_charging/plans/" + str(payload["data"]["plan"]),
                "")
        else:
            pub_error(payload, connection_id, "Die ID ist größer als die maximal vergebene ID.")

    def addChargeTemplateTimeChargingPlan(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neuer Zeitladen-Plan erstellt werden soll.
        """
        new_id = self.max_id_charge_template_time_charging_plan + 1
        MainLogger().info("Neues Zeitladen-Template mit ID " + str(new_id) + " zu Template " +
                          str(payload["data"]["template"]) + " hinzugefügt.")
        time_charging_plan_default = ev.get_charge_template_time_charging_plan_default()
        Pub().pub(
            "openWB/set/vehicle/template/charge_template/" + str(payload["data"]["template"]) +
            "/time_charging/plans/" + str(new_id),
            time_charging_plan_default)
        self.max_id_charge_template_time_charging_plan = new_id
        Pub().pub(
            "openWB/set/command/max_id/charge_template_time_charging_plan", new_id)

    def removeChargeTemplateTimeChargingPlan(self, connection_id: str, payload: dict) -> None:
        """ löscht einen Zeitladen-Plan.
        """
        if self.max_id_charge_template_time_charging_plan >= payload["data"]["plan"]:
            MainLogger().info(
                "Zeitladen-Template mit ID " + str(payload["data"]["plan"]) + " zu Template " +
                str(payload["data"]["template"]) + " gelöscht.")
            Pub().pub(
                "openWB/vehicle/template/charge_template/" + str(payload["data"]["template"]) +
                "/time_charging/plans/" + str(payload["data"]["plan"]),
                "")
        else:
            pub_error(payload, connection_id, "Die ID ist größer als die maximal vergebene ID.")

    def addComponent(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem eine neue Komponente erstellt werden soll.
        """
        new_id = self.max_id_component + 1
        MainLogger().info(
            "Neue Komponente vom Typ"+str(payload["data"]["type"])+" mit ID "+str(new_id)+" hinzugefügt.")
        component = importlib.import_module(
            "."+payload["data"]["deviceType"]+"."+payload["data"]["type"], "modules")
        component_default = component.get_default_config()
        component_default["id"] = new_id
        if payload["data"]["type"] == "counter":
            try:
                data.data.counter_data["all"].hierarchy_add_item_below(
                    "counter"+str(new_id), data.data.counter_data["all"].get_evu_counter())
            except TypeError:
                # es gibt noch keinen EVU-Zähler
                Pub().pub("openWB/set/counter/get/hierarchy",
                          [{"id": "counter"+str(new_id), "children": []}] +
                          data.data.counter_data["all"].data["get"]["hierarchy"])
            default_config = counter.get_counter_default_config()
            for item in default_config:
                Pub().pub("openWB/set/counter/"+str(new_id)+"/config/"+item, default_config[item])
        Pub().pub("openWB/set/system/device/"+str(payload["data"]["deviceId"]
                                                  )+"/component/"+str(new_id)+"/config", component_default)
        self.max_id_component = self.max_id_component + 1
        Pub().pub("openWB/set/command/max_id/component",
                  self.max_id_component)

    def removeComponent(self, connection_id: str, payload: dict) -> None:
        """ löscht eine Komponente.
        """
        if self.max_id_component >= payload["data"]["id"]:
            MainLogger().info("Komponente mit ID "+str(payload["data"]["id"])+" gelöscht.")
            branch = "system/device/"+str(payload["data"]["deviceId"])+"/component/"+str(payload["data"]["id"])
            ProcessBrokerBranch(branch).remove_topics()
        else:
            pub_error(payload, connection_id, "Die ID ist größer als die maximal vergebene ID.")

    def addEvTemplate(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neues EV-Template erstellt werden soll.
        """
        new_id = self.max_id_ev_template + 1
        MainLogger().info("Neues EV-Template mit ID "+str(new_id)+" hinzugefügt.")
        ev_template_default = ev.get_ev_template_default()
        Pub().pub("openWB/set/vehicle/template/ev_template/" +
                  str(new_id), ev_template_default)
        self.max_id_ev_template = new_id
        Pub().pub("openWB/set/command/max_id/ev_template", new_id)

    def removeEvTemplate(self, connection_id: str, payload: dict) -> None:
        """ löscht ein EV-Template.
        """
        if self.max_id_ev_template >= payload["data"]["id"]:
            if payload["data"]["id"] > 0:
                MainLogger().info("EV-Template mit ID " +
                                  str(payload["data"]["id"])+" gelöscht.")
                Pub().pub("openWB/vehicle/template/ev_template/" +
                          str(payload["data"]["id"]), "")
            else:
                pub_error(payload, connection_id, "EV-Vorlage mit ID 0 darf nicht gelöscht werden.")
        else:
            pub_error(payload, connection_id, "Die ID ist größer als die maximal vergebene ID.")

    def addVehicle(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neues Vehicle erstellt werden soll.
        """
        new_id = self.max_id_vehicle + 1
        MainLogger().info("Neues EV mit ID "+str(new_id)+" hinzugefügt.")
        vehicle_default = ev.get_vehicle_default()
        for default in vehicle_default:
            Pub().pub("openWB/set/vehicle/"+str(new_id)+"/" +
                      str(default), vehicle_default[default])
        self.max_id_vehicle = self.max_id_vehicle + 1
        Pub().pub("openWB/set/command/max_id/vehicle", self.max_id_vehicle)
        # Default-Mäßig werden die Templates 0 zugewiesen, wenn diese noch nicht existieren -> anlegen
        if self.max_id_charge_template == -1:
            self.addChargeTemplate("addVehicle", {})
        if self.max_id_ev_template == -1:
            self.addEvTemplate("addVehicle", {})

    def removeVehicle(self, connection_id: str, payload: dict) -> None:
        """ löscht ein Vehicle.
        """
        if self.max_id_vehicle >= payload["data"]["id"]:
            if payload["data"]["id"] > 0:
                MainLogger().info(
                    "EV mit ID "+str(payload["data"]["id"])+" gelöscht.")
                Pub().pub("openWB/vehicle/"+str(payload["data"]["id"]), "")
                ProcessBrokerBranch(
                    "vehicle"+str(payload["data"]["id"])).remove_topics()
            else:
                pub_error(payload, connection_id, "Vehicle mit ID 0 darf nicht gelöscht werden.")
        else:
            pub_error(payload, connection_id, "Die ID ist größer als die maximal vergebene ID.")

    def sendDebug(self, connection_id: str, payload: dict) -> None:
        parent_file = Path(__file__).resolve().parents[2]
        Pub().pub("openWB/set/system/debug_level", 2)
        subprocess.run([str(parent_file / "runs" / "send_debug.sh"),
                        str(payload["data"]["message"]),
                        str(payload["data"]["email"])])
        Pub().pub("openWB/set/system/debug_level", 0)

    def getDailyLog(self, connection_id: str, payload: dict) -> None:
        measurement_log.pub_daily_log(payload["data"]["day"])

    def getMonthlyLog(self, connection_id: str, payload: dict) -> None:
        measurement_log.pub_monthly_log(payload["data"]["month"])

    def initCloud(self, connection_id: str, payload: dict) -> None:
        parent_file = Path(__file__).resolve().parents[2]
        try:
            result = subprocess.check_output(
                ["php", "-f", str(parent_file / "runs" / "cloudRegister.php"), json.dumps(payload["data"])]
            )
            # exitstatus = 0 is success, std_out contains json: {"username", "password"}
            result_dict = json.loads(result)
            connect_payload = {
                "data": result_dict
            }
            self.connectCloud(connection_id, connect_payload)
        except subprocess.CalledProcessError as error:
            # exitstatus = 1 is failure, std_out contains error message
            pub_error(payload, connection_id, error.output.decode("utf-8"))

    def connectCloud(self, connection_id: str, payload: dict) -> None:
        cloud_config = bridge.get_cloud_config()
        cloud_config["remote"]["username"] = payload["data"]["username"]
        cloud_config["remote"]["password"] = payload["data"]["password"]
        cloud_config["remote"]["prefix"] = payload["data"]["username"] + "/"
        self.addMqttBridge(connection_id, payload, cloud_config)

    def addMqttBridge(self, connection_id: str, payload: dict,
                      bridge_default: dict = bridge.get_default_config()) -> None:
        new_id = self.max_id_mqtt_bridge + 1
        MainLogger().info("Neue Bridge mit ID "+str(new_id)+" hinzugefügt.")
        Pub().pub("openWB/set/system/mqtt/bridge/"+str(new_id), bridge_default)
        self.max_id_mqtt_bridge = self.max_id_mqtt_bridge + 1
        Pub().pub("openWB/set/command/max_id/mqtt_bridge", self.max_id_mqtt_bridge)

    def removeMqttBridge(self, connection_id: str, payload: dict) -> None:
        if self.max_id_mqtt_bridge >= payload["data"]["bridge"]:
            MainLogger().info("Bridge mit ID "+str(payload["data"]["bridge"])+" gelöscht.")
            Pub().pub("openWB/system/mqtt/bridge/"+str(payload["data"]["bridge"]), "")
        else:
            pub_error(payload, connection_id, "Die ID ist größer als die maximal vergebene ID.")


class ErrorHandlingContext:
    def __init__(self, payload: dict, connection_id: str):
        self.payload = payload
        self.connection_id = connection_id

    def __enter__(self):
        return None

    def __exit__(self, exception_type, exception, exception_traceback) -> bool:
        if isinstance(exception, Exception):
            pub_error(self.payload, self.connection_id, "Es ist ein interner Fehler aufgetreten: " +
                      traceback.format_exc())
            return True
        else:
            return False


def pub_error(payload: dict, connection_id: str, error_str: str) -> None:
    """ sendet ein Fehler-Topic, warum der Befehl nicht ausgeführt werden konnte.
    """
    try:
        error_payload = {
            "command": payload["command"],
            "data": payload["data"],
            "error": error_str
        }
        Pub().pub("openWB/set/command/" +
                  str(connection_id)+"/error", error_payload)
        MainLogger().error("Befehl konnte nicht ausgeführt werden: "+str(error_payload))
    except Exception:
        MainLogger().exception("Fehler im Command-Modul")


class ProcessBrokerBranch:
    def __init__(self, topic_str: str) -> None:
        self.topic_str = topic_str

    def remove_topics(self):
        """ löscht einen Topic-Zweig auf dem Broker. Payload "" löscht nur ein einzelnes Topic.
        """
        try:
            self.__connect_to_broker(self.__on_message_rm)
        except Exception:
            MainLogger().exception("Fehler im Command-Modul")

    def get_max_id(self, default: int):
        try:
            self.max_id = default
            self.search_str = "openWB/" + self.topic_str.replace("+", "[0-9]+")
            self.__connect_to_broker(self.__on_message_max_id)
            return self.max_id
        except Exception:
            MainLogger().exception("Fehler im Command-Modul")

    def __connect_to_broker(self, on_message):
        """ abonniert alle Topics.
        """
        try:
            mqtt_broker_ip = "localhost"
            client = mqtt.Client(
                "openWB-processBrokerBranch-" + str(self.__getserial()))

            client.on_connect = self.__on_connect
            client.on_message = on_message

            client.connect(mqtt_broker_ip, 1886)
            client.loop_start()
            time.sleep(0.5)
            client.loop_stop()

        except Exception:
            MainLogger().exception("Fehler im Command-Modul")

    def __on_connect(self, client, userdata, flags, rc):
        """ connect to broker and subscribe to set topics
        """
        try:
            client.subscribe("openWB/"+self.topic_str+"/#", 2)
        except Exception:
            MainLogger().exception("Fehler im Command-Modul")

    def __on_message_rm(self, client, userdata, msg):
        """ wartet auf eingehende Topics.
        """
        try:
            if str(msg.payload.decode("utf-8")) != '':
                MainLogger().debug("Gelöschtes Topic: "+str(msg.topic))
                Pub().pub(msg.topic, "")
                if "openWB/system/device/" in msg.topic and "component" in msg.topic and "config" in msg.topic:
                    payload = json.loads(str(msg.payload.decode("utf-8")))
                    if payload["type"] == "counter":
                        data.data.counter_data["all"].hierarchy_remove_item("counter"+str(payload["id"]))
                    if payload["type"] == "inverter":
                        module_branch = "openWB/pv/"+str(payload["id"])
                    else:
                        module_branch = "openWB/"+payload["type"]+"/"+str(payload["id"])
                    client.subscribe(module_branch+"/#", 2)
        except Exception:
            MainLogger().exception("Fehler im Command-Modul")

    def __on_message_max_id(self, client, userdata, msg):
        try:
            result = re.search('^('+self.search_str+'/*).*$', msg.topic)
            if result is not None:
                topic_found = result.group(1)
                topic_rest = msg.topic.replace(topic_found, "")
                current_id_regex = re.search('^([0-9]+)/*.*$', topic_rest)
                if current_id_regex is not None:
                    current_id = int(current_id_regex.group(1))
                    self.max_id = max(current_id, self.max_id)
        except Exception:
            MainLogger().exception("Fehler im Command-Modul")

    def __getserial(self):
        """ Extract serial from cpuinfo file
        """
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line[0:6] == 'Serial':
                        return line[10:26]
                return "0000000000000000"
        except Exception:
            MainLogger().exception("Fehler im Command-Modul")
