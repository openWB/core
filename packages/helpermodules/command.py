import importlib
import json
import logging
import subprocess
import time
from typing import List
import re
import traceback
from pathlib import Path

from helpermodules import measurement_log
from helpermodules.broker import InternalBrokerClient
from helpermodules.pub import Pub
from control import bridge, chargelog, chargepoint, data, ev, counter, pv
from modules.common.component_type import ComponentType, special_to_general_type_mapping, type_to_topic_mapping
import dataclass_utils

log = logging.getLogger(__name__)


class Command:
    """
    """
    # Tuple: (Name der maximalen ID, Topic zur Ermittlung, Default-Wert)
    MAX_IDS = [("autolock_plan", "chargepoint/template/+/autolock", -1),
               ("mqtt_bridge", "system/mqtt/bridge", -1),
               ("charge_template", "vehicle/template/charge_template", 0),
               ("charge_template_scheduled_plan",
                "vehicle/template/charge_template/+/chargemode/scheduled_charging/plans",
                -1),
               ("charge_template_time_charging_plan", "vehicle/template/charge_template/+/time_charging/plans", -1),
               ("chargepoint_template", "chargepoint/template", 0),
               ("device", "system/device", -1),
               ("ev_template", "vehicle/template/ev_template", 0),
               ("vehicle", "vehicle", 0)]

    def __init__(self):
        try:
            self.__get_max_ids()
            self.__get_max_id_by_json_object("hierarchy", "counter/get/hierarchy/", -1)
        except Exception:
            log.exception("Fehler im Command-Modul")

    def __get_max_ids(self) -> None:
        """ ermittelt die maximale ID vom Broker """
        try:
            received_topics = ProcessBrokerBranch("").get_max_id()
            for id_topic, topic_str, default in self.MAX_IDS:
                max_id = default
                for topic in received_topics:
                    search_str = "openWB/" + topic_str.replace("+", "[0-9]+")
                    result = re.search('^('+search_str+'/*).*$', topic)
                    if result is not None:
                        topic_found = result.group(1)
                        topic_rest = topic.replace(topic_found, "")
                        current_id_regex = re.search('^([0-9]+)/*.*$', topic_rest)
                        if current_id_regex is not None:
                            current_id = int(current_id_regex.group(1))
                            max_id = max(current_id, max_id)
                Pub().pub("openWB/set/command/max_id/"+id_topic, max_id)
        except Exception:
            log.exception("Fehler im Command-Modul")

    def __get_max_id_by_json_object(self, id_topic: str, topic: str, default: int) -> None:
        """ ermittelt die maximale ID vom Broker """
        try:
            hierarchy = ProcessBrokerBranch(topic).get_payload()
            max_id = counter.get_max_id_in_hierarchy(hierarchy, default)
            Pub().pub(f'openWB/set/command/max_id/{id_topic}', max_id)
        except Exception:
            log.exception("Fehler im Command-Modul")

    def sub_commands(self):
        """ abonniert alle Topics.
        """
        try:
            # kurze Pause, damit die ID vom Broker ermittelt werden können. Sonst werden noch vorher die retained
            # Topics empfangen, was zu doppelten Meldungen im Protokoll führt.
            time.sleep(1)
            self.internal_broker_client = InternalBrokerClient("command", self.on_connect, self.on_message)
            self.internal_broker_client.start_infinite_loop()
        except Exception:
            log.exception("Fehler im Command-Modul")

    def on_connect(self, client, userdata, flags, rc):
        """ connect to broker and subscribe to set topics
        """
        try:
            client.subscribe("openWB/command/#", 2)
        except Exception:
            log.exception("Fehler im Command-Modul")

    def on_message(self, client, userdata, msg):
        """ wartet auf eingehende Topics.
        """
        try:
            if str(msg.payload.decode("utf-8")) != '':
                if "todo" in msg.topic:
                    payload = json.loads(str(msg.payload.decode("utf-8")))
                    connection_id = msg.topic.split("/")[2]
                    log.debug(f'Befehl: {payload}, Connection-ID: {connection_id}')
                    # Methoden-Name = Befehl
                    try:
                        func = getattr(self, payload["command"])
                        with ErrorHandlingContext(payload, connection_id):
                            func(connection_id, payload)
                    except Exception:
                        pub_error_user(payload, connection_id, "Zu dem Befehl wurde keine Methode gefunden.")
                    Pub().pub(msg.topic, "")
                elif "max_id" in msg.topic:
                    self.__process_max_id_topic(msg)
        except Exception:
            log.exception("Fehler im Command-Modul")

    def __process_max_id_topic(self, msg, no_log: bool = False) -> None:
        try:
            payload = json.loads(str(msg.payload.decode("utf-8")))
            result = re.search("/([a-z,A-Z,0-9,_]+)(?!.*/)", msg.topic)
            if result is not None:
                var = result.group(1)
                # Der Variablen-Name für die maximale ID setzt sich aus "max_id_" und dem Topic-Namen nach dem letzten /
                # zusammen.
                setattr(self, f'max_id_{var}', payload)
                log.debug(f'Max ID {var} {payload}')
        except Exception:
            log.exception("Fehler im Command-Modul")

    def addDevice(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neues Device erstellt werden soll.
        """
        new_id = self.max_id_device + 1
        dev = importlib.import_module("."+payload["data"]["type"]+".device", "modules")
        device_default = dataclass_utils.asdict(dev.device_descriptor.configuration_factory())
        device_default["id"] = new_id
        Pub().pub(f'openWB/set/system/device/{new_id}/config', device_default)
        self.max_id_device = self.max_id_device + 1
        Pub().pub("openWB/set/command/max_id/device", self.max_id_device)
        pub_success_user(
            payload, connection_id,
            f'Neues Device vom Typ \'{payload["data"]["type"]}\' mit ID \'{new_id}\' hinzugefügt.')

    def removeDevice(self, connection_id: str, payload: dict) -> None:
        """ löscht ein Device.
        """
        if self.max_id_device >= payload["data"]["id"]:
            ProcessBrokerBranch(f'system/device/{payload["data"]["id"]}/').remove_topics()
            pub_success_user(payload, connection_id, f'Gerät mit ID \'{payload["data"]["id"]}\' gelöscht.')
        else:
            pub_error_user(
                payload, connection_id,
                f'Die ID \'{payload["data"]["id"]}\' ist größer als die maximal vergebene ID \'{self.max_id_device}\'.')

    def addChargepoint(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neuer Chargepoint erstellt werden soll.
        """
        new_id = self.max_id_hierarchy + 1
        log.info(f'Neuer Ladepunkt mit ID \'{new_id}\' wird hinzugefügt.')
        chargepoint_default = chargepoint.get_chargepoint_default()
        # chargepoint_default["id"] = new_id
        module = importlib.import_module("." + payload["data"]["type"] + ".chargepoint_module", "modules")
        chargepoint_default = {**chargepoint_default, **module.get_default_config()}
        chargepoint_default["id"] = new_id
        chargepoint_default["type"] = payload["data"]["type"]
        try:
            evu_counter = data.data.counter_data["all"].get_id_evu_counter()
            data.data.counter_data["all"].hierarchy_add_item_below(
                new_id, ComponentType.CHARGEPOINT, evu_counter)
            Pub().pub(f'openWB/set/chargepoint/{new_id}/config', chargepoint_default)
            Pub().pub(f'openWB/set/chargepoint/{new_id}/set/manual_lock', False)
            self.max_id_hierarchy = self.max_id_hierarchy + 1
            Pub().pub("openWB/set/command/max_id/hierarchy", self.max_id_hierarchy)
            if self.max_id_chargepoint_template == -1:
                self.addChargepointTemplate("addChargepoint", {})
            if self.max_id_vehicle == -1:
                self.addVehicle("addChargepoint", {})
            pub_success_user(payload, connection_id, f'Neuer Ladepunkt mit ID \'{new_id}\' wurde erstellt.')
        except (TypeError, IndexError):
            pub_error_user(payload, connection_id, "Bitte zuerst einen EVU-Zähler konfigurieren!")

    def removeChargepoint(self, connection_id: str, payload: dict) -> None:
        """ löscht ein Chargepoint.
        """
        if self.max_id_hierarchy >= payload["data"]["id"]:
            data.data.counter_data["all"].hierarchy_remove_item(payload["data"]["id"])
            ProcessBrokerBranch(f'chargepoint/{payload["data"]["id"]}/').remove_topics()
            pub_success_user(payload, connection_id, f'Ladepunkt mit ID \'{payload["data"]["id"]}\' gelöscht.')
        else:
            pub_error_user(
                payload, connection_id,
                f'Die ID \'{payload["data"]["id"]}\' ist größer als die maximal vergebene '
                f'ID \'{self.max_id_hierarchy}\'.')

    def addChargepointTemplate(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem eine neue Ladepunkt-Vorlage erstellt werden soll.
        """
        new_id = self.max_id_chargepoint_template + 1
        default = chargepoint.get_chargepoint_template_default()
        default["id"] = new_id
        Pub().pub(f'openWB/set/chargepoint/template/{new_id}', default)
        self.max_id_chargepoint_template = self.max_id_chargepoint_template + 1
        Pub().pub("openWB/set/command/max_id/chargepoint_template",
                  self.max_id_chargepoint_template)
        pub_success_user(
            payload, connection_id,
            f'Neue Ladepunkt-Vorlage mit ID \'{new_id}\' hinzugefügt.')

    def removeChargepointTemplate(self, connection_id: str, payload: dict) -> None:
        """ löscht eine Ladepunkt-Vorlage.
        """
        if self.max_id_chargepoint_template >= payload["data"]["id"]:
            if payload["data"]["id"] > 0:
                ProcessBrokerBranch(f'chargepoint/template/{payload["data"]["id"]}/').remove_topics()
                pub_success_user(payload, connection_id,
                                 f'Ladepunkt-Vorlage mit ID \'{payload["data"]["id"]}\' gelöscht.')
            else:
                pub_error_user(payload, connection_id, "Ladepunkt-Vorlage mit ID 0 darf nicht gelöscht werden.")
        else:
            pub_error_user(
                payload, connection_id,
                f'Die ID \'{payload["data"]["id"]}\' ist größer als '
                f'die maximal vergebene ID \'{self.max_id_chargepoint_template}\'.')

    def addAutolockPlan(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neuer Zielladen-Plan erstellt werden soll.
        """
        new_id = self.max_id_autolock_plan + 1
        default = chargepoint.get_autolock_plan_default()
        Pub().pub(f'openWB/set/chargepoint/template/{payload["data"]["template"]}/autolock/{new_id}',
                  default)
        self.max_id_autolock_plan = new_id
        Pub().pub("openWB/set/command/max_id/autolock_plan", new_id)
        pub_success_user(
            payload, connection_id,
            f'Neuer Autolock-Plan mit ID \'{new_id}\' zu Template '
            f'\'{payload["data"]["template"]}\' hinzugefügt.')

    def removeAutolockPlan(self, connection_id: str, payload: dict) -> None:
        """ löscht einen Zielladen-Plan.
        """
        if self.max_id_autolock_plan >= payload["data"]["plan"]:
            Pub().pub(
                f'openWB/chargepoint/template/{payload["data"]["template"]}'
                f'/autolock/{payload["data"]["plan"]}',
                "")
            pub_success_user(
                payload, connection_id,
                f'Autolock-Plan mit ID \'{payload["data"]["plan"]}\' zu Template '
                f'\'{payload["data"]["template"]}\' gelöscht.')
        else:
            pub_error_user(
                payload, connection_id,
                f'Die ID \'{payload["data"]["plan"]}\' ist größer als die '
                f'maximal vergebene ID \'{self.max_id_autolock_plan}\'.')

    def addChargeTemplate(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem eine neue Lade-Vorlage erstellt werden soll.
        """
        new_id = self.max_id_charge_template + 1
        charge_template_default = ev.get_charge_template_default()
        Pub().pub("openWB/set/vehicle/template/charge_template/" +
                  str(new_id), charge_template_default)
        self.max_id_charge_template = new_id
        Pub().pub("openWB/set/command/max_id/charge_template", new_id)
        pub_success_user(payload, connection_id,
                         f'Neues Lade-Template mit ID \'{new_id}\' hinzugefügt.')

    def removeChargeTemplate(self, connection_id: str, payload: dict) -> None:
        """ löscht eine Lade-Vorlage.
        """
        if self.max_id_charge_template >= payload["data"]["id"]:
            if payload["data"]["id"] > 0:
                Pub().pub(f'openWB/vehicle/template/charge_template/{payload["data"]["id"]}', "")
                pub_success_user(
                    payload, connection_id,
                    f'Lade-Template mit ID \'{payload["data"]["id"]}\' gelöscht.')
            else:
                pub_error_user(payload, connection_id, "Ladevorlage mit ID 0 darf nicht gelöscht werden.")
        else:
            pub_error_user(payload, connection_id, "Die ID ist größer als die maximal vergebene ID.")

    def addChargeTemplateSchedulePlan(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neuer Zielladen-Plan erstellt werden soll.
        """
        new_id = self.max_id_charge_template_scheduled_plan + 1
        charge_template_default = dataclass_utils.asdict(ev.ScheduledChargingPlan())
        Pub().pub(
            f'openWB/set/vehicle/template/charge_template/{payload["data"]["template"]}'
            f'/chargemode/scheduled_charging/plans/{new_id}',
            charge_template_default)
        self.max_id_charge_template_scheduled_plan = new_id
        Pub().pub(
            "openWB/set/command/max_id/charge_template_scheduled_plan", new_id)
        pub_success_user(
            payload, connection_id,
            f'Neues Zielladen-Template mit ID \'{new_id}\' zu Template '
            f'\'{payload["data"]["template"]}\' hinzugefügt.')

    def removeChargeTemplateSchedulePlan(self, connection_id: str, payload: dict) -> None:
        """ löscht einen Zielladen-Plan.
        """
        if self.max_id_charge_template_scheduled_plan >= payload["data"]["plan"]:
            Pub().pub(
                f'openWB/vehicle/template/charge_template/{payload["data"]["template"]}'
                f'/chargemode/scheduled_charging/plans/{payload["data"]["plan"]}',
                "")
            pub_success_user(
                payload, connection_id,
                f'Zielladen-Template mit ID \'{payload["data"]["plan"]}\' zu Template '
                f'{payload["data"]["template"]}\' gelöscht.')
        else:
            pub_error_user(
                payload, connection_id,
                f'Die ID \'{payload["data"]["plan"]}\' ist größer als die maximal vergebene '
                f'ID \'{self.max_id_charge_template_scheduled_plan}\'.')

    def addChargeTemplateTimeChargingPlan(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neuer Zeitladen-Plan erstellt werden soll.
        """
        new_id = self.max_id_charge_template_time_charging_plan + 1
        time_charging_plan_default = dataclass_utils.asdict(ev.TimeChargingPlan())
        Pub().pub(
            f'openWB/set/vehicle/template/charge_template/{payload["data"]["template"]}'
            f'/time_charging/plans/{new_id}',
            time_charging_plan_default)
        self.max_id_charge_template_time_charging_plan = new_id
        Pub().pub(
            "openWB/set/command/max_id/charge_template_time_charging_plan", new_id)
        pub_success_user(
            payload, connection_id,
            f'Neues Zeitladen-Template mit ID \'{new_id}\' zu Template '
            f'{payload["data"]["template"]}\' hinzugefügt.')

    def removeChargeTemplateTimeChargingPlan(self, connection_id: str, payload: dict) -> None:
        """ löscht einen Zeitladen-Plan.
        """
        if self.max_id_charge_template_time_charging_plan >= payload["data"]["plan"]:
            Pub().pub(
                f'openWB/vehicle/template/charge_template/{payload["data"]["template"]}'
                f'/time_charging/plans/{payload["data"]["plan"]}',
                "")
            pub_success_user(
                payload, connection_id,
                f'Zeitladen-Template mit ID \'{payload["data"]["plan"]}\' zu Template '
                f'\'{payload["data"]["template"]}\' gelöscht.')
        else:
            pub_error_user(payload, connection_id, "Die ID ist größer als die maximal vergebene ID.")

    def addComponent(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem eine neue Komponente erstellt werden soll.
        """
        new_id = self.max_id_hierarchy + 1
        component = importlib.import_module(
            "."+payload["data"]["deviceType"]+"."+payload["data"]["type"], "modules")
        component_default = dataclass_utils.asdict(component.component_descriptor.configuration_factory())
        component_default["id"] = new_id
        general_type = special_to_general_type_mapping(payload["data"]["type"])
        try:
            data.data.counter_data["all"].hierarchy_add_item_below(
                new_id, general_type, data.data.counter_data["all"].get_id_evu_counter())
        except (TypeError, IndexError):
            if general_type == ComponentType.COUNTER:
                # es gibt noch keinen EVU-Zähler
                Pub().pub("openWB/set/counter/get/hierarchy",
                          [{
                              "id": new_id,
                              "type": ComponentType.COUNTER.value,
                              "children": []
                          }] +
                          data.data.counter_data["all"].data["get"]["hierarchy"])
            else:
                pub_error_user(payload, connection_id, "Bitte erst einen EVU-Zähler konfigurieren!")
                return
        # Bei Zählern müssen noch Standardwerte veröffentlicht werden.
        if general_type == ComponentType.COUNTER:
            default_config = counter.get_counter_default_config()
            for item in default_config:
                Pub().pub(f'openWB/set/counter/{new_id}/config/{item}', default_config[item])
        elif general_type == ComponentType.INVERTER:
            default_config = pv.get_inverter_default_config()
            for item in default_config:
                Pub().pub(f'openWB/set/pv/{new_id}/config/{item}', default_config[item])
        Pub().pub(f'openWB/set/system/device/{payload["data"]["deviceId"]}/component/{new_id}/config',
                  component_default)
        self.max_id_hierarchy = self.max_id_hierarchy + 1
        Pub().pub("openWB/set/command/max_id/hierarchy",
                  self.max_id_hierarchy)
        pub_success_user(
            payload, connection_id,
            f'Neue Komponente vom Typ \'{payload["data"]["type"]}\' mit ID \'{new_id}\' hinzugefügt.')

    def removeComponent(self, connection_id: str, payload: dict) -> None:
        """ löscht eine Komponente.
        """
        if self.max_id_hierarchy >= payload["data"]["id"]:
            branch = f'system/device/{payload["data"]["deviceId"]}/component/{payload["data"]["id"]}/'
            ProcessBrokerBranch(branch).remove_topics()
            pub_success_user(
                payload, connection_id,
                f'Komponente mit ID \'{payload["data"]["id"]}\' gelöscht.')
        else:
            pub_error_user(payload, connection_id, "Die ID ist größer als die maximal vergebene ID.")

    def addEvTemplate(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neues EV-Template erstellt werden soll.
        """
        new_id = self.max_id_ev_template + 1
        ev_template_default = dataclass_utils.asdict(ev.EvTemplateData())
        Pub().pub(f'openWB/set/vehicle/template/ev_template/{new_id}', ev_template_default)
        self.max_id_ev_template = new_id
        Pub().pub("openWB/set/command/max_id/ev_template", new_id)
        pub_success_user(
            payload, connection_id,
            f'Neues EV-Template mit ID \'{new_id}\' hinzugefügt.')

    def removeEvTemplate(self, connection_id: str, payload: dict) -> None:
        """ löscht ein EV-Template.
        """
        if self.max_id_ev_template >= payload["data"]["id"]:
            if payload["data"]["id"] > 0:
                Pub().pub(f'openWB/vehicle/template/ev_template/{payload["data"]["id"]}', "")
                pub_success_user(
                    payload, connection_id,
                    f'EV-Template mit ID \'{payload["data"]["id"]}\' gelöscht.')
            else:
                pub_error_user(payload, connection_id, "EV-Vorlage mit ID 0 darf nicht gelöscht werden.")
        else:
            pub_error_user(payload, connection_id, "Die ID ist größer als die maximal vergebene ID.")

    def addVehicle(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neues Vehicle erstellt werden soll.
        """
        new_id = self.max_id_vehicle + 1
        vehicle_default = ev.get_vehicle_default()
        for default in vehicle_default:
            Pub().pub(f"openWB/set/vehicle/{new_id}/{default}", vehicle_default[default])
        Pub().pub(f"openWB/set/vehicle/{new_id}/soc_module/config", {"type": None, "configuration": {}})
        self.max_id_vehicle = self.max_id_vehicle + 1
        Pub().pub("openWB/set/command/max_id/vehicle", self.max_id_vehicle)
        # Default-Mäßig werden die Templates 0 zugewiesen, wenn diese noch nicht existieren -> anlegen
        if self.max_id_charge_template == -1:
            self.addChargeTemplate("addVehicle", {})
        if self.max_id_ev_template == -1:
            self.addEvTemplate("addVehicle", {})
        pub_success_user(payload, connection_id, f'Neues EV mit ID \'{new_id}\' hinzugefügt.')

    def removeVehicle(self, connection_id: str, payload: dict) -> None:
        """ löscht ein Vehicle.
        """
        if self.max_id_vehicle >= payload["data"]["id"]:
            if payload["data"]["id"] > 0:
                Pub().pub(f'openWB/vehicle/{payload["data"]["id"]}', "")
                ProcessBrokerBranch(f'vehicle/{payload["data"]["id"]}/').remove_topics()
                pub_success_user(
                    payload, connection_id,
                    f'EV mit ID \'{payload["data"]["id"]}\' gelöscht.')
            else:
                pub_error_user(payload, connection_id, "Vehicle mit ID 0 darf nicht gelöscht werden.")
        else:
            pub_error_user(payload, connection_id, "Die ID ist größer als die maximal vergebene ID.")

    def sendDebug(self, connection_id: str, payload: dict) -> None:
        pub_success_user(payload, connection_id, "Systembericht wird erstellt...")
        parent_file = Path(__file__).resolve().parents[2]
        previous_log_level = data.data.system_data["system"].data["debug_level"]
        Pub().pub("openWB/set/system/debug_level", 10)
        subprocess.run([str(parent_file / "runs" / "send_debug.sh"),
                        json.dumps(payload["data"])])
        Pub().pub("openWB/set/system/debug_level", previous_log_level)
        pub_success_user(payload, connection_id, "Systembericht wurde versandt.")

    def getChargeLog(self, connection_id: str, payload: dict) -> None:
        Pub().pub(f'openWB/set/log/{connection_id}/data', chargelog.get_log_data(payload["data"]))

    def getDailyLog(self, connection_id: str, payload: dict) -> None:
        Pub().pub(f'openWB/set/log/daily/{payload["data"]["day"]}',
                  measurement_log.get_daily_log(payload["data"]["day"]))

    def getMonthlyLog(self, connection_id: str, payload: dict) -> None:
        Pub().pub(f'openWB/set/log/monthly/{payload["data"]["month"]}',
                  measurement_log.get_monthly_log(payload["data"]["month"]))

    def initCloud(self, connection_id: str, payload: dict) -> None:
        parent_file = Path(__file__).resolve().parents[2]
        try:
            result = subprocess.check_output(
                ["php", "-f", str(parent_file / "runs" / "cloudRegister.php"), json.dumps(payload["data"])]
            )
            # exit status = 0 is success, std_out contains json: {"username", "password"}
            result_dict = json.loads(result)
            connect_payload = {
                "data": result_dict
            }
            self.connectCloud(connection_id, connect_payload)
            pub_success_user(payload, connection_id, "Verbindung zur Cloud wurde eingerichtet.")
        except subprocess.CalledProcessError as error:
            # exit status = 1 is failure, std_out contains error message
            pub_error_user(payload, connection_id, error.output.decode("utf-8"))

    def connectCloud(self, connection_id: str, payload: dict) -> None:
        cloud_config = bridge.get_cloud_config()
        cloud_config["remote"]["username"] = payload["data"]["username"]
        cloud_config["remote"]["password"] = payload["data"]["password"]
        cloud_config["remote"]["prefix"] = payload["data"]["username"] + "/"
        self.addMqttBridge(connection_id, payload, cloud_config)
        pub_success_user(payload, connection_id, "Verbindung zur Cloud wurde angelegt.")

    def addMqttBridge(self, connection_id: str, payload: dict,
                      bridge_default: dict = bridge.get_default_config()) -> None:
        new_id = self.max_id_mqtt_bridge + 1
        Pub().pub(f'openWB/set/system/mqtt/bridge/{new_id}', bridge_default)
        self.max_id_mqtt_bridge = self.max_id_mqtt_bridge + 1
        Pub().pub("openWB/set/command/max_id/mqtt_bridge", self.max_id_mqtt_bridge)
        pub_success_user(payload, connection_id, f'Neue Bridge mit ID \'{new_id}\' hinzugefügt.')

    def removeMqttBridge(self, connection_id: str, payload: dict) -> None:
        if self.max_id_mqtt_bridge >= payload["data"]["bridge"]:
            Pub().pub(f'openWB/system/mqtt/bridge/{payload["data"]["bridge"]}', "")
            pub_success_user(payload, connection_id, f'Bridge mit ID \'{payload["data"]["bridge"]}\' gelöscht.')
        else:
            pub_error_user(payload, connection_id,
                           f'Die ID \'{payload["data"]["bridge"]}\' ist größer als die maximal vergebene '
                           f'ID \'{self.max_id_mqtt_bridge}\'.')

    def systemReboot(self, connection_id: str, payload: dict) -> None:
        pub_success_user(payload, connection_id, "Neustart wird ausgeführt.")
        parent_file = Path(__file__).resolve().parents[2]
        subprocess.run([str(parent_file / "runs" / "reboot.sh")])

    def systemShutdown(self, connection_id: str, payload: dict) -> None:
        pub_success_user(payload, connection_id, "OpenWB wird heruntergefahren.")
        parent_file = Path(__file__).resolve().parents[2]
        subprocess.run([str(parent_file / "runs" / "shutdown.sh")])

    def systemUpdate(self, connection_id: str, payload: dict) -> None:
        log.info("Update requested")
        parent_file = Path(__file__).resolve().parents[2]
        if "branch" in payload["data"] and "tag" in payload["data"]:
            pub_success_user(
                payload, connection_id,
                f'Wechsel auf Zweig \'{payload["data"]["branch"]}\' Tag \'{payload["data"]["tag"]}\' gestartet.')
            subprocess.run([
                str(parent_file / "runs" / "update_self.sh"),
                str(payload["data"]["branch"]),
                str(payload["data"]["tag"])])
        else:
            pub_success_user(payload, connection_id, "Update gestartet.")
            subprocess.run([str(parent_file / "runs" / "update_self.sh")])

    def systemFetchVersions(self, connection_id: str, payload: dict) -> None:
        log.info("Fetch versions requested")
        parent_file = Path(__file__).resolve().parents[2]
        result = subprocess.run([str(parent_file / "runs" / "update_available_versions.sh")])
        if result.returncode == 0:
            pub_success_user(payload, connection_id, "Versionsliste erfolgreich aktualisiert.")
        else:
            pub_error_user(
                payload, connection_id,
                f'Version-Status: {result.returncode}<br />Meldung: {result.stdout.decode("utf-8")}')

    def createBackup(self, connection_id: str, payload: dict) -> None:
        pub_success_user(payload, connection_id, "Backup wird erstellt.")
        parent_file = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            [str(parent_file / "runs" / "backup.sh"),
             "1" if "use_extended_filename" in payload["data"] and payload["data"]["use_extended_filename"] else "0"],
            stdout=subprocess.PIPE)
        if result.returncode == 0:
            file_name = result.stdout.decode("utf-8").rstrip('\n')
            file_link = "/openWB/data/backup/" + file_name
            pub_success_user(payload, connection_id,
                             "Backup erfolgreich erstellt.<br />"
                             f'Jetzt <a href="{file_link}" target="_blank">herunterladen</a>.')
        else:
            pub_error_user(payload, connection_id,
                           f'Backup-Status: {result.returncode}<br />Meldung: {result.stdout.decode("utf-8")}')

    def restoreBackup(self, connection_id: str, payload: dict) -> None:
        parent_file = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            [str(parent_file / "runs" / "prepare_restore.sh")],
            stdout=subprocess.PIPE)
        if result.returncode == 0:
            pub_success_user(payload, connection_id,
                             "Wiederherstellung vorbereitet. OpenWB wird jetzt zum Abschluss neu gestartet.")
        else:
            pub_error_user(payload, connection_id,
                           f'Restore-Status: {result.returncode}<br />Meldung: {result.stdout.decode("utf-8")}')


class ErrorHandlingContext:
    def __init__(self, payload: dict, connection_id: str):
        self.payload = payload
        self.connection_id = connection_id

    def __enter__(self):
        return None

    def __exit__(self, exception_type, exception, exception_traceback) -> bool:
        if isinstance(exception, Exception):
            pub_error_global(self.payload, self.connection_id,
                             f'Es ist ein interner Fehler aufgetreten: {traceback.format_exc()}')
            return True
        else:
            return False


def pub_success_user(payload: dict, connection_id: str, message: str) -> None:
    try:
        log.info("pub_success: " + message)
        now = time.time()
        success_payload = {
            "source": "command",
            "type": "success",
            "message": message,
            "timestamp": int(now)
        }
        Pub().pub(f'openWB/set/command/{connection_id}/messages/{(now * 1000):.0f}', success_payload)
        log.info(f'Befehl erfolgreich ausgeführt: {message}')
    except Exception:
        log.exception("Fehler im Command-Modul")


def pub_error_user(payload: dict, connection_id: str, error_str: str) -> None:
    """ sendet ein Fehler-Topic, warum der Befehl nicht ausgeführt werden konnte.
    """
    try:
        now = time.time()
        error_payload = {
            "source": "command",
            "type": "danger",
            "message": error_str,
            "timestamp": int(now)
        }
        Pub().pub(f'openWB/set/command/{connection_id}/messages/{(now * 1000):.0f}', error_payload)
        log.error(f'Befehl konnte nicht ausgeführt werden: {error_payload}')
    except Exception:
        log.exception("Fehler im Command-Modul")


def pub_error_global(payload: dict, connection_id: str, error_str: str) -> None:
    """ sendet ein Fehler-Topic, warum der Befehl nicht ausgeführt werden konnte.
    """
    try:
        error_payload = {
            "command": payload["command"],
            "data": payload["data"],
            "error": error_str
        }
        Pub().pub(f'openWB/set/command/{connection_id}/error', error_payload)
        log.error(f'Befehl konnte nicht ausgeführt werden: {error_payload}')
    except Exception:
        log.exception("Fehler im Command-Modul")


class ProcessBrokerBranch:
    def __init__(self, topic_str: str) -> None:
        self.topic_str = topic_str

    def get_payload(self):
        self.payload: str
        InternalBrokerClient("processBrokerBranch", self.on_connect, self.__get_payload).start_finite_loop()
        return json.loads(self.payload)

    def remove_topics(self):
        """ löscht einen Topic-Zweig auf dem Broker. Payload "" löscht nur ein einzelnes Topic.
        """
        InternalBrokerClient("processBrokerBranch", self.on_connect, self.__on_message_rm).start_finite_loop()

    def get_max_id(self) -> List[str]:
        try:
            self.received_topics = []
            InternalBrokerClient("processBrokerBranch", self.on_connect, self.__on_message_max_id).start_finite_loop()
            return self.received_topics
        except Exception:
            log.exception("Fehler im Command-Modul")
            return []

    def on_connect(self, client, userdata, flags, rc):
        """ connect to broker and subscribe to set topics
        """
        client.subscribe(f'openWB/{self.topic_str}#', 2)
        client.subscribe(f'openWB/set/{self.topic_str}#', 2)

    def __on_message_rm(self, client, userdata, msg):
        if str(msg.payload.decode("utf-8")) != '':
            log.debug(f'Gelöschtes Topic: {msg.topic}')
            Pub().pub(msg.topic, "")
            if "openWB/system/device/" in msg.topic and "component" in msg.topic and "config" in msg.topic:
                payload = json.loads(str(msg.payload.decode("utf-8")))
                topic = type_to_topic_mapping(payload["type"])
                data.data.counter_data["all"].hierarchy_remove_item(payload["id"])
                client.subscribe(f'openWB/{topic}/{payload["id"]}/#', 2)

    def __on_message_max_id(self, client, userdata, msg):
        self.received_topics.append(msg.topic)

    def __get_payload(self, client, userdata, msg):
        self.payload = msg.payload
