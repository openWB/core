from dataclasses import asdict
import importlib
import json
import logging
import subprocess
import threading
import time
from typing import Dict, List, Optional
import re
import traceback
from pathlib import Path

import paho.mqtt.client as mqtt
from control.chargelog import chargelog
from control.chargepoint import chargepoint
from control.chargepoint.chargepoint_template import get_autolock_plan_default, get_chargepoint_template_default

# ToDo: move to module commands if implemented
from control.ev.charge_template import get_new_charge_template
from control.ev.ev_template import EvTemplateData
from helpermodules import pub
from helpermodules.abstract_plans import ScheduledChargingPlan, TimeChargingPlan
from helpermodules.utils.run_command import run_command
from modules.backup_clouds.onedrive.api import generateMSALAuthCode, retrieveMSALTokens

from helpermodules.broker import InternalBrokerClient
from helpermodules.data_migration.data_migration import MigrateData
from helpermodules.measurement_logging.process_log import get_daily_log, get_monthly_log, get_yearly_log
from helpermodules.messaging import MessageType, pub_user_message
from helpermodules.create_debug import create_debug_log
from helpermodules.pub import Pub, pub_single
from helpermodules.subdata import SubData
from helpermodules.utils.topic_parser import decode_payload
from control import bat, bridge, data, counter, counter_all, pv
from control.ev import ev
from modules.chargepoints.internal_openwb.chargepoint_module import ChargepointModule
from modules.chargepoints.internal_openwb.config import InternalChargepointMode
from modules.common.component_type import ComponentType, special_to_general_type_mapping, type_to_topic_mapping
import dataclass_utils
from modules.common.configurable_vehicle import GeneralVehicleConfig


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

    def __init__(self, event_command_completed: threading.Event):
        try:
            self.event_command_completed = event_command_completed
            self._get_max_ids()
            self._get_max_id_by_json_object("hierarchy", "counter/get/hierarchy/", -1)
        except Exception:
            log.exception("Fehler im Command-Modul")

    def _get_max_ids(self) -> None:
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
                setattr(self, f'max_id_{id_topic}', max_id)
                Pub().pub("openWB/set/command/max_id/"+id_topic, max_id)
        except Exception:
            log.exception("Fehler im Command-Modul")

    def _get_max_id_by_json_object(self, id_topic: str, topic: str, default: int) -> None:
        """ ermittelt die maximale ID vom Broker """
        try:
            hierarchy = ProcessBrokerBranch(topic).get_payload()
            max_id = counter_all.get_max_id_in_hierarchy(hierarchy, default)
            setattr(self, f'max_id_{id_topic}', max_id)
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

    def on_connect(self, client: mqtt.Client, userdata, flags: dict, rc: int):
        """ connect to broker and subscribe to set topics
        """
        try:
            client.subscribe("openWB/command/#", 2)
        except Exception:
            log.exception("Fehler im Command-Modul")

    def on_message(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
        """ wartet auf eingehende Topics.
        """
        try:
            if decode_payload(msg.payload) != '':
                if "todo" in msg.topic:
                    payload = decode_payload(msg.payload)
                    with CompleteCommandContext(self.event_command_completed):
                        connection_id = msg.topic.split("/")[2]
                        log.debug(f'Befehl: {payload}, Connection-ID: {connection_id}')
                        # Methoden-Name = Befehl
                        try:
                            func = getattr(self, payload["command"])
                            with ErrorHandlingContext(payload, connection_id):
                                func(connection_id, payload)
                        except Exception:
                            pub_user_message(payload, connection_id, f'Unbekannter Befehl: \'{payload["command"]}\'',
                                             MessageType.ERROR)
                        Pub().pub(msg.topic, "")
        except Exception:
            log.exception("Fehler im Command-Modul")

    def addDevice(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neues Device erstellt werden soll.
        """
        new_id = self.max_id_device + 1
        dev = importlib.import_module(f'.devices.{payload["data"]["vendor"]}'
                                      f'.{payload["data"]["type"]}.device',
                                      "modules")
        device_default = dataclass_utils.asdict(dev.device_descriptor.configuration_factory())
        device_default["id"] = new_id
        Pub().pub(f'openWB/set/system/device/{new_id}/config', device_default)
        self.max_id_device = self.max_id_device + 1
        Pub().pub("openWB/set/command/max_id/device", self.max_id_device)
        pub_user_message(
            payload, connection_id,
            f'Neues Gerät vom Typ \'{payload["data"]["type"]}\' mit ID \'{new_id}\' hinzugefügt.',
            MessageType.SUCCESS)

    def removeDevice(self, connection_id: str, payload: dict) -> None:
        """ löscht ein Device.
        """
        if self.max_id_device >= payload["data"]["id"]:
            ProcessBrokerBranch(f'system/device/{payload["data"]["id"]}/').remove_topics()
            pub_user_message(payload, connection_id, f'Gerät mit ID \'{payload["data"]["id"]}\' gelöscht.',
                             MessageType.SUCCESS)
        else:
            pub_user_message(
                payload, connection_id,
                f'Die ID \'{payload["data"]["id"]}\' ist größer als die maximal vergebene ID \'{self.max_id_device}\'.',
                MessageType.ERROR)

    def addChargepoint(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neuer Chargepoint erstellt werden soll.
        """
        def setup_added_chargepoint():
            Pub().pub(f'openWB/chargepoint/{new_id}/config', chargepoint_config)
            Pub().pub(f'openWB/chargepoint/{new_id}/set/manual_lock', False)
            {Pub().pub(f"openWB/chargepoint/{new_id}/get/"+k, v) for (k, v) in asdict(chargepoint.Get()).items()}
            self.max_id_hierarchy = self.max_id_hierarchy + 1
            Pub().pub("openWB/set/command/max_id/hierarchy", self.max_id_hierarchy)
            if self.max_id_chargepoint_template == -1:
                self.addChargepointTemplate("addChargepoint", {})
            if self.max_id_vehicle == -1:
                self.addVehicle("addChargepoint", {})
            pub_user_message(payload, connection_id, f'Neuer Ladepunkt mit ID \'{new_id}\' wurde erstellt.',
                             MessageType.SUCCESS)
        new_id = self.max_id_hierarchy + 1
        log.info(f'Neuer Ladepunkt mit ID \'{new_id}\' wird hinzugefügt.')
        chargepoint_config = chargepoint.get_chargepoint_config_default()
        # chargepoint_default["id"] = new_id
        module = importlib.import_module(".chargepoints." + payload["data"]["type"] + ".chargepoint_module", "modules")
        chargepoint_config.update(dataclass_utils.asdict(
            module.chargepoint_descriptor.configuration_factory()).items())
        check_num_msg = self._check_max_num_of_internal_chargepoints(chargepoint_config)
        if check_num_msg is not None:
            pub_user_message(
                payload, connection_id, f"{check_num_msg} Wenn Sie weitere Ladepunkte anbinden wollen, müssen Sie "
                "diese als secondary openWB anbinden. Die weiteren Ladepunkte in den Steuerungsmodus 'secondary'"
                " versetzen.", MessageType.ERROR)
            return
        chargepoint_config["id"] = new_id
        try:
            evu_counter = data.data.counter_all_data.get_id_evu_counter()
            data.data.counter_all_data.hierarchy_add_item_below(
                new_id, ComponentType.CHARGEPOINT, evu_counter)
            Pub().pub("openWB/set/counter/get/hierarchy", data.data.counter_all_data.data.get.hierarchy)
            setup_added_chargepoint()
        except (TypeError, IndexError):
            if chargepoint_config["type"] == 'internal_openwb' and SubData.general_data.data.extern:
                # es gibt noch keinen EVU-Zähler
                hierarchy = ([{
                              "id": new_id,
                              "type": ComponentType.CHARGEPOINT.value,
                              "children": []
                              }] +
                             data.data.counter_all_data.data.get.hierarchy)
                Pub().pub("openWB/set/counter/get/hierarchy", hierarchy)
                data.data.counter_all_data.data.get.hierarchy = hierarchy
                setup_added_chargepoint()
            else:
                pub_user_message(payload, connection_id,
                                 "Bitte zuerst einen EVU-Zähler konfigurieren oder in den Steuerungsmodus 'secondary' "
                                 "umschalten.",
                                 MessageType.ERROR)

    MAX_NUM_OF_DUOS_REACHED = ("Es können maximal zwei interne Ladepunkte für eine openWB Series 1/2 Duo konfiguriert "
                               "werden.")
    MAX_NUM_REACHED = ("Es kann maximal ein interner Ladepunkt für eine openWB Series 1/2 Buchse, Custom, "
                       "Standard oder Standard+ konfiguriert werden. Wenn ein zweiter Ladepunkt für eine "
                       "Duo hinzugefügt werden soll, muss auch für den ersten Ladepunkt Bauart 'Duo' "
                       "gewählt und gespeichert werden.")

    def _check_max_num_of_internal_chargepoints(self, config: Dict) -> Optional[str]:
        if config["type"] == 'internal_openwb':
            count_series_socket = 0
            count_duo = 0
            for cp in SubData.cp_data.values():
                if isinstance(cp.chargepoint.chargepoint_module, ChargepointModule):
                    if (cp.chargepoint.chargepoint_module.config.configuration.mode ==
                            InternalChargepointMode.DUO.value):
                        count_duo += 1
                    else:
                        count_series_socket += 1
            if count_series_socket == 0 and count_duo == 0:
                return None
            elif count_duo == 1:
                # Wenn es genau eine Duo gibt, darf noch ein LP hinzugefügt werden.
                return None
            elif count_duo >= 1:
                return self.MAX_NUM_OF_DUOS_REACHED
            else:
                return self.MAX_NUM_REACHED
        else:
            return None

    def removeChargepoint(self, connection_id: str, payload: dict) -> None:
        """ löscht ein Chargepoint.
        """
        if self.max_id_hierarchy < payload["data"]["id"]:
            pub_user_message(
                payload, connection_id,
                f'Die ID \'{payload["data"]["id"]}\' ist größer als die maximal vergebene '
                f'ID \'{self.max_id_hierarchy}\'.', MessageType.ERROR)
        ProcessBrokerBranch(f'chargepoint/{payload["data"]["id"]}/').remove_topics()
        data.data.counter_all_data.hierarchy_remove_item(payload["data"]["id"])
        Pub().pub("openWB/set/counter/get/hierarchy", data.data.counter_all_data.data.get.hierarchy)
        pub_user_message(payload, connection_id,
                         f'Ladepunkt mit ID \'{payload["data"]["id"]}\' gelöscht.', MessageType.SUCCESS)

    def addChargepointTemplate(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neues Ladepunkt-Profil erstellt werden soll.
        """
        new_id = self.max_id_chargepoint_template + 1
        default = get_chargepoint_template_default()
        default["id"] = new_id
        Pub().pub(f'openWB/set/chargepoint/template/{new_id}', default)
        self.max_id_chargepoint_template = self.max_id_chargepoint_template + 1
        Pub().pub("openWB/set/command/max_id/chargepoint_template",
                  self.max_id_chargepoint_template)
        pub_user_message(
            payload, connection_id,
            f'Neues Ladepunkt-Profil mit ID \'{new_id}\' hinzugefügt.',
            MessageType.SUCCESS)

    def removeChargepointTemplate(self, connection_id: str, payload: dict) -> None:
        """ löscht ein Ladepunkt-Profil.
        """
        if self.max_id_chargepoint_template < payload["data"]["id"]:
            pub_user_message(
                payload, connection_id,
                f'Die ID \'{payload["data"]["id"]}\' ist größer als '
                f'die maximal vergebene ID \'{self.max_id_chargepoint_template}\'.', MessageType.ERROR)
        if payload["data"]["id"] > 0:
            ProcessBrokerBranch(f'chargepoint/template/{payload["data"]["id"]}/').remove_topics()
            pub_user_message(payload, connection_id,
                             f'Ladepunkt-Profil mit ID \'{payload["data"]["id"]}\' gelöscht.',
                             MessageType.SUCCESS)
        else:
            pub_user_message(payload, connection_id, "Ladepunkt-Profil mit ID 0 darf nicht gelöscht werden.",
                             MessageType.ERROR)

    def addAutolockPlan(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neuer Zielladen-Plan erstellt werden soll.
        """
        new_id = self.max_id_autolock_plan + 1
        default = get_autolock_plan_default()
        Pub().pub(f'openWB/set/chargepoint/template/{payload["data"]["template"]}/autolock/{new_id}',
                  default)
        self.max_id_autolock_plan = new_id
        Pub().pub("openWB/set/command/max_id/autolock_plan", new_id)
        pub_user_message(
            payload, connection_id,
            f'Neuer Autolock-Plan mit ID \'{new_id}\' zu Profil '
            f'\'{payload["data"]["template"]}\' hinzugefügt.',
            MessageType.SUCCESS)

    def removeAutolockPlan(self, connection_id: str, payload: dict) -> None:
        """ löscht einen Zielladen-Plan.
        """
        if self.max_id_autolock_plan < payload["data"]["plan"]:
            pub_user_message(
                payload, connection_id,
                f'Die ID \'{payload["data"]["plan"]}\' ist größer als die '
                f'maximal vergebene ID \'{self.max_id_autolock_plan}\'.', MessageType.ERROR)
        Pub().pub(
            f'openWB/chargepoint/template/{payload["data"]["template"]}'
            f'/autolock/{payload["data"]["plan"]}',
            "")
        pub_user_message(
            payload, connection_id,
            f'Autolock-Plan mit ID \'{payload["data"]["plan"]}\' vom Profil '
            f'\'{payload["data"]["template"]}\' gelöscht.',
            MessageType.SUCCESS)

    def addChargeTemplate(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neues Lade-Profil erstellt werden soll.
        """
        new_id = self.max_id_charge_template + 1
        charge_template_default = get_new_charge_template()
        Pub().pub("openWB/set/vehicle/template/charge_template/" +
                  str(new_id), charge_template_default)
        self.max_id_charge_template = new_id
        Pub().pub("openWB/set/command/max_id/charge_template", new_id)
        pub_user_message(payload, connection_id,
                         f'Neues Lade-Profil mit ID \'{new_id}\' hinzugefügt.',
                         MessageType.SUCCESS)

    def removeChargeTemplate(self, connection_id: str, payload: dict) -> None:
        """ löscht ein Lade-Profil.
        """
        if self.max_id_charge_template < payload["data"]["id"]:
            pub_user_message(payload, connection_id, "Die ID ist größer als die maximal vergebene ID.",
                             MessageType.ERROR)
        if payload["data"]["id"] > 0:
            ProcessBrokerBranch(f'vehicle/template/charge_template/{payload["data"]["id"]}/').remove_topics()
            pub_user_message(
                payload, connection_id,
                f'Lade-Profil mit ID \'{payload["data"]["id"]}\' gelöscht.',
                MessageType.SUCCESS)
        else:
            pub_user_message(payload, connection_id, "Lade-Profil mit ID 0 darf nicht gelöscht werden.",
                             MessageType.ERROR)

    def addChargeTemplateSchedulePlan(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neuer Zielladen-Plan erstellt werden soll.
        """
        new_id = self.max_id_charge_template_scheduled_plan + 1
        charge_template_default = ScheduledChargingPlan()
        charge_template_default.id = new_id
        Pub().pub(
            f'openWB/set/vehicle/template/charge_template/{payload["data"]["template"]}'
            f'/chargemode/scheduled_charging/plans/{new_id}',
            dataclass_utils.asdict(charge_template_default))
        self.max_id_charge_template_scheduled_plan = new_id
        Pub().pub(
            "openWB/set/command/max_id/charge_template_scheduled_plan", new_id)
        pub_user_message(
            payload, connection_id,
            f'Neuer Zielladen-Plan mit ID \'{new_id}\' zu Profil '
            f'\'{payload["data"]["template"]}\' hinzugefügt.',
            MessageType.SUCCESS)

    def removeChargeTemplateSchedulePlan(self, connection_id: str, payload: dict) -> None:
        """ löscht einen Zielladen-Plan.
        """
        if self.max_id_charge_template_scheduled_plan < payload["data"]["plan"]:
            pub_user_message(
                payload, connection_id,
                f'Die ID \'{payload["data"]["plan"]}\' ist größer als die maximal vergebene '
                f'ID \'{self.max_id_charge_template_scheduled_plan}\'.', MessageType.ERROR)
        Pub().pub(
            f'openWB/vehicle/template/charge_template/{payload["data"]["template"]}'
            f'/chargemode/scheduled_charging/plans/{payload["data"]["plan"]}',
            "")
        pub_user_message(
            payload, connection_id,
            f'Zielladen-Plan mit ID \'{payload["data"]["plan"]}\' von Profil '
            f'{payload["data"]["template"]}\' gelöscht.',
            MessageType.SUCCESS)

    def addChargeTemplateTimeChargingPlan(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neuer Zeitladen-Plan erstellt werden soll.
        """
        new_id = self.max_id_charge_template_time_charging_plan + 1
        time_charging_plan_default = TimeChargingPlan()
        time_charging_plan_default.id = new_id
        Pub().pub(
            f'openWB/set/vehicle/template/charge_template/{payload["data"]["template"]}'
            f'/time_charging/plans/{new_id}',
            dataclass_utils.asdict(time_charging_plan_default))
        self.max_id_charge_template_time_charging_plan = new_id
        Pub().pub(
            "openWB/set/command/max_id/charge_template_time_charging_plan", new_id)
        pub_user_message(
            payload, connection_id,
            f'Neuer Zeitladen-Plan mit ID \'{new_id}\' zu Profil '
            f'{payload["data"]["template"]}\' hinzugefügt.', MessageType.SUCCESS)

    def removeChargeTemplateTimeChargingPlan(self, connection_id: str, payload: dict) -> None:
        """ löscht einen Zeitladen-Plan.
        """
        if self.max_id_charge_template_time_charging_plan < payload["data"]["plan"]:
            pub_user_message(payload, connection_id, "Die ID ist größer als die maximal vergebene ID.",
                             MessageType.ERROR)
        Pub().pub(
            f'openWB/vehicle/template/charge_template/{payload["data"]["template"]}'
            f'/time_charging/plans/{payload["data"]["plan"]}',
            "")
        pub_user_message(
            payload, connection_id,
            f'Zeitladen-Plan mit ID \'{payload["data"]["plan"]}\' zu Profil '
            f'\'{payload["data"]["template"]}\' gelöscht.', MessageType.SUCCESS)

    def addComponent(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem eine neue Komponente erstellt werden soll.
        """
        def set_default(topic: str, defaults: dict):
            for k, v in defaults.items():
                Pub().pub(f'{topic}/{k}', v)
        new_id = self.max_id_hierarchy + 1
        component = importlib.import_module(f'.devices.{payload["data"]["deviceVendor"]}'
                                            f'.{payload["data"]["deviceType"]}.{payload["data"]["type"]}',
                                            "modules")
        component_default = dataclass_utils.asdict(component.component_descriptor.configuration_factory())
        component_default["id"] = new_id
        general_type = special_to_general_type_mapping(payload["data"]["type"])
        try:
            data.data.counter_all_data.hierarchy_add_item_below_evu(new_id, general_type)
            Pub().pub("openWB/set/counter/get/hierarchy", data.data.counter_all_data.data.get.hierarchy)
        except ValueError:
            pub_user_message(payload, connection_id, counter_all.CounterAll.MISSING_EVU_COUNTER, MessageType.ERROR)
            return
        # Bei Zählern müssen noch Standardwerte veröffentlicht werden.
        if general_type == ComponentType.BAT:
            topic = f"openWB/set/bat/{new_id}"
            set_default(f"{topic}/get", asdict(bat.Get()))
        elif general_type == ComponentType.COUNTER:
            topic = f"openWB/set/counter/{new_id}"
            set_default(f"{topic}/config", counter.get_counter_default_config())
            set_default(f"{topic}/get", asdict(counter.Get()))
        elif general_type == ComponentType.INVERTER:
            topic = f"openWB/set/pv/{new_id}"
            set_default(f"{topic}/config", pv.get_inverter_default_config())
            set_default(f"{topic}/get", asdict(pv.Get()))
        Pub().pub(f'openWB/set/system/device/{payload["data"]["deviceId"]}/component/{new_id}/config',
                  component_default)
        self.max_id_hierarchy = self.max_id_hierarchy + 1
        Pub().pub("openWB/set/command/max_id/hierarchy",
                  self.max_id_hierarchy)
        pub_user_message(
            payload, connection_id,
            f'Neue Komponente vom Typ \'{payload["data"]["type"]}\' mit ID \'{new_id}\' hinzugefügt.',
            MessageType.SUCCESS)

    def removeComponent(self, connection_id: str, payload: dict) -> None:
        """ löscht eine Komponente.
        """
        if self.max_id_hierarchy < payload["data"]["id"]:
            pub_user_message(payload, connection_id,
                             "Die ID ist größer als die maximal vergebene ID.", MessageType.ERROR)
        branch = f'system/device/{payload["data"]["deviceId"]}/component/{payload["data"]["id"]}/'
        ProcessBrokerBranch(branch).remove_topics()
        pub_user_message(
            payload, connection_id,
            f'Komponente mit ID \'{payload["data"]["id"]}\' gelöscht.', MessageType.SUCCESS)

    def addEvTemplate(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neues Fahrzeug-Profil erstellt werden soll.
        """
        new_id = self.max_id_ev_template + 1
        ev_template_default = dataclass_utils.asdict(EvTemplateData())
        Pub().pub(f'openWB/set/vehicle/template/ev_template/{new_id}', ev_template_default)
        self.max_id_ev_template = new_id
        Pub().pub("openWB/set/command/max_id/ev_template", new_id)
        pub_user_message(
            payload, connection_id,
            f'Neues Fahrzeug-Profil mit ID \'{new_id}\' hinzugefügt.', MessageType.SUCCESS)

    def removeEvTemplate(self, connection_id: str, payload: dict) -> None:
        """ löscht ein Fahrzeug-Profil.
        """
        if self.max_id_ev_template < payload["data"]["id"]:
            pub_user_message(payload, connection_id,
                             "Die ID ist größer als die maximal vergebene ID.", MessageType.ERROR)
        if payload["data"]["id"] > 0:
            ProcessBrokerBranch(f'vehicle/template/ev_template/{payload["data"]["id"]}/').remove_topics()
            pub_user_message(
                payload, connection_id,
                f'Fahrzeug-Profil mit ID \'{payload["data"]["id"]}\' gelöscht.', MessageType.SUCCESS)
        else:
            pub_user_message(payload, connection_id,
                             "Fahrzeug-Profil mit ID 0 darf nicht gelöscht werden.", MessageType.ERROR)

    def addVehicle(self, connection_id: str, payload: dict) -> None:
        """ sendet das Topic, zu dem ein neues Vehicle erstellt werden soll.
        """
        new_id = self.max_id_vehicle + 1
        vehicle_default = ev.get_vehicle_default()
        for default in vehicle_default:
            Pub().pub(f"openWB/set/vehicle/{new_id}/{default}", vehicle_default[default])
        Pub().pub(f"openWB/set/vehicle/{new_id}/soc_module/config", {"type": None, "configuration": {}})
        Pub().pub(f"openWB/set/vehicle/{new_id}/soc_module/general_config",
                  dataclass_utils.asdict(GeneralVehicleConfig()))
        self.max_id_vehicle = self.max_id_vehicle + 1
        Pub().pub("openWB/set/command/max_id/vehicle", self.max_id_vehicle)
        # Default-Mäßig werden die Profile 0 zugewiesen, wenn diese noch nicht existieren -> anlegen
        if self.max_id_charge_template == -1:
            self.addChargeTemplate("addVehicle", {})
        if self.max_id_ev_template == -1:
            self.addEvTemplate("addVehicle", {})
        pub_user_message(payload, connection_id, f'Neues EV mit ID \'{new_id}\' hinzugefügt.', MessageType.SUCCESS)

    def removeVehicle(self, connection_id: str, payload: dict) -> None:
        """ löscht ein Vehicle.
        """
        if self.max_id_vehicle < payload["data"]["id"]:
            pub_user_message(payload, connection_id,
                             "Die ID ist größer als die maximal vergebene ID.", MessageType.ERROR)
        if payload["data"]["id"] > 0:
            Pub().pub(f'openWB/vehicle/{payload["data"]["id"]}', "")
            ProcessBrokerBranch(f'vehicle/{payload["data"]["id"]}/').remove_topics()
            pub_user_message(
                payload, connection_id,
                f'EV mit ID \'{payload["data"]["id"]}\' gelöscht.', MessageType.SUCCESS)
        else:
            pub_user_message(payload, connection_id,
                             "Vehicle mit ID 0 darf nicht gelöscht werden.", MessageType.ERROR)

    def sendDebug(self, connection_id: str, payload: dict) -> None:
        pub_user_message(payload, connection_id, "Systembericht wird erstellt...", MessageType.INFO)
        previous_log_level = SubData.system_data["system"].data["debug_level"]
        create_debug_log(payload["data"])
        Pub().pub("openWB/set/system/debug_level", previous_log_level)
        pub_user_message(payload, connection_id, "Systembericht wurde versandt.", MessageType.SUCCESS)

    def getChargeLog(self, connection_id: str, payload: dict) -> None:
        Pub().pub(f'openWB/set/log/{connection_id}/data', chargelog.get_log_data(payload["data"]))

    def getDailyLog(self, connection_id: str, payload: dict) -> None:
        Pub().pub(f'openWB/set/log/daily/{payload["data"]["day"]}',
                  get_daily_log(payload["data"]["day"]))

    def getMonthlyLog(self, connection_id: str, payload: dict) -> None:
        Pub().pub(f'openWB/set/log/monthly/{payload["data"]["month"]}',
                  get_monthly_log(payload["data"]["month"]))

    def getYearlyLog(self, connection_id: str, payload: dict) -> None:
        Pub().pub(f'openWB/set/log/yearly/{payload["data"]["year"]}',
                  get_yearly_log(payload["data"]["year"]))

    def initCloud(self, connection_id: str, payload: dict) -> None:
        parent_file = Path(__file__).resolve().parents[2]
        result = run_command(
            ["php", "-f", str(parent_file / "runs" / "cloudRegister.php"), json.dumps(payload["data"])]
        )
        # exit status = 0 is success, std_out contains json: {"username", "password"}
        result_dict = json.loads(result)
        connect_payload = {
            "data": result_dict
        }
        connect_payload["data"]["partner"] = payload["data"]["partner"]
        self.connectCloud(connection_id, connect_payload)
        pub_user_message(payload, connection_id, "Verbindung zur Cloud wurde eingerichtet.", MessageType.SUCCESS)

    def connectCloud(self, connection_id: str, payload: dict) -> None:
        cloud_config = bridge.get_cloud_config()
        cloud_config["remote"]["username"] = payload["data"]["username"]
        cloud_config["remote"]["password"] = payload["data"]["password"]
        cloud_config["remote"]["prefix"] = payload["data"]["username"] + "/"
        cloud_config["access"]["partner"] = payload["data"]["partner"]
        self.addMqttBridge(connection_id, payload, cloud_config)
        pub_user_message(payload, connection_id, "Verbindung zur Cloud wurde angelegt.", MessageType.SUCCESS)

    def addMqttBridge(self, connection_id: str, payload: dict,
                      bridge_default: dict = bridge.get_default_config()) -> None:
        if ProcessBrokerBranch("system/mqtt/bridge/").check_mqtt_bridge_exists(bridge_default["name"]):
            pub_user_message(payload, connection_id, ('Es existiert bereits eine Brücke mit dem Namen '
                             f'{bridge_default["name"]}.'), MessageType.ERROR)
        else:
            new_id = self.max_id_mqtt_bridge + 1
            Pub().pub(f'openWB/set/system/mqtt/bridge/{new_id}', bridge_default)
            self.max_id_mqtt_bridge = self.max_id_mqtt_bridge + 1
            Pub().pub("openWB/set/command/max_id/mqtt_bridge", self.max_id_mqtt_bridge)
            pub_user_message(payload, connection_id,
                             f'Neue Brücke mit ID \'{new_id}\' hinzugefügt.', MessageType.SUCCESS)

    def removeMqttBridge(self, connection_id: str, payload: dict) -> None:
        if self.max_id_mqtt_bridge >= payload["data"]["bridge"]:
            Pub().pub(f'openWB/system/mqtt/bridge/{payload["data"]["bridge"]}', "")
            pub_user_message(payload, connection_id,
                             f'Bridge mit ID \'{payload["data"]["bridge"]}\' gelöscht.', MessageType.SUCCESS)
        else:
            pub_user_message(payload, connection_id,
                             f'Die ID \'{payload["data"]["bridge"]}\' ist größer als die maximal vergebene '
                             f'ID \'{self.max_id_mqtt_bridge}\'.', MessageType.ERROR)

    def chargepointReboot(self, connection_id: str, payload: dict) -> None:
        pub.pub_single("openWB/set/command/primary/todo",
                       {"command": "systemReboot", "data": {}},
                       hostname=SubData.cp_data[f'cp{payload["data"]["chargepoint"]}'
                                                ].chargepoint.chargepoint_module.config.configuration.ip_address)

    def chargepointShutdown(self, connection_id: str, payload: dict) -> None:
        pub.pub_single("openWB/set/command/primary/todo",
                       {"command": "systemReboot", "data": {}},
                       hostname=SubData.cp_data[payload["data"]["chargepoint"]
                                                ].chargepoint.chargepoint_module.config.configuration.ip_address)

    def systemReboot(self, connection_id: str, payload: dict) -> None:
        pub_user_message(payload, connection_id, "Neustart wird ausgeführt.", MessageType.INFO)
        parent_file = Path(__file__).resolve().parents[2]
        run_command([str(parent_file / "runs" / "reboot.sh")])

    def systemShutdown(self, connection_id: str, payload: dict) -> None:
        pub_user_message(payload, connection_id, "openWB wird heruntergefahren.", MessageType.INFO)
        parent_file = Path(__file__).resolve().parents[2]
        run_command([str(parent_file / "runs" / "shutdown.sh")])

    def systemUpdate(self, connection_id: str, payload: dict) -> None:
        log.info("Update requested")
        # notify system about running update, notify about end update in script
        Pub().pub("openWB/system/update_in_progress", True)
        if SubData.system_data["system"].data["backup_cloud"]["backup_before_update"]:
            try:
                self.createCloudBackup(connection_id, {})
            except Exception:
                pub_user_message(payload, connection_id,
                                 ("Fehler beim Erstellen der Cloud-Sicherung. Update abgebrochen! "
                                  "Bitte die Cloud-Konfiguration überprüfen! Die Option " +
                                  "Sicherung vor System Update kann unter Datenverwaltung deaktiviert werden."),
                                 MessageType.ERROR)
                log.exception("Fehler beim Erstellen der Cloud-Sicherung: ")
                Pub().pub("openWB/system/update_in_progress", False)
                return
        parent_file = Path(__file__).resolve().parents[2]
        if "branch" in payload["data"] and "tag" in payload["data"]:
            pub_user_message(
                payload, connection_id,
                f'Wechsel auf Zweig \'{payload["data"]["branch"]}\' Tag \'{payload["data"]["tag"]}\' gestartet.',
                MessageType.SUCCESS)
            run_command([
                str(parent_file / "runs" / "update_self.sh"),
                str(payload["data"]["branch"]),
                str(payload["data"]["tag"])])
        else:
            pub_user_message(payload, connection_id, "Update gestartet.", MessageType.INFO)
            run_command([
                str(parent_file / "runs" / "update_self.sh"),
                SubData.system_data["system"].data["current_branch"]])

    def systemFetchVersions(self, connection_id: str, payload: dict) -> None:
        log.info("Fetch versions requested")
        pub_user_message(payload, connection_id, "Versionsliste wird aktualisiert...", MessageType.INFO)
        parent_file = Path(__file__).resolve().parents[2]
        run_command([str(parent_file / "runs" / "update_available_versions.sh")])
        pub_user_message(payload, connection_id, "Versionsliste erfolgreich aktualisiert.", MessageType.SUCCESS)

    def createBackup(self, connection_id: str, payload: dict) -> None:
        pub_user_message(payload, connection_id, "Backup wird erstellt...", MessageType.INFO)
        parent_file = Path(__file__).resolve().parents[2]
        result = run_command(
            [str(parent_file / "runs" / "backup.sh"),
             "1" if "use_extended_filename" in payload["data"] and payload["data"]["use_extended_filename"] else "0"])
        file_name = result.rstrip('\n')
        file_link = "/openWB/data/backup/" + file_name
        pub_user_message(payload, connection_id,
                         "Backup erfolgreich erstellt.<br />"
                         f'Jetzt <a href="{file_link}" target="_blank">herunterladen</a>.', MessageType.SUCCESS)

    def createCloudBackup(self, connection_id: str, payload: dict) -> None:
        if SubData.system_data["system"].backup_cloud is not None:
            pub_user_message(payload, connection_id, ("Backup wird erstellt. Dieser Vorgang kann je nach Umfang der "
                             "Logdaten und Upload-Geschwindigkeit des Cloud-Dienstes einige Zeit in Anspruch nehmen."),
                             MessageType.INFO)
            SubData.system_data["system"].create_backup_and_send_to_cloud()
            pub_user_message(payload, connection_id, "Backup erfolgreich erstellt.<br />", MessageType.SUCCESS)
        else:
            pub_user_message(payload, connection_id,
                             "Es ist keine Backup-Cloud konfiguriert.<br />", MessageType.WARNING)

    def restoreBackup(self, connection_id: str, payload: dict) -> None:
        parent_file = Path(__file__).resolve().parents[2]
        run_command([str(parent_file / "runs" / "prepare_restore.sh")])
        pub_user_message(payload, connection_id,
                         "Wiederherstellung wurde vorbereitet. openWB wird jetzt zum Abschluss neu gestartet.",
                         MessageType.INFO)
        self.systemReboot(connection_id, payload)

    # ToDo: move to module commands if implemented
    def requestMSALAuthCode(self, connection_id: str, payload: dict) -> None:
        ''' fordert einen Authentifizierungscode für MSAL (Microsoft Authentication Library)
        an um Onedrive Backup zu ermöglichen'''
        cloudbackupconfig = SubData.system_data["system"].backup_cloud
        if cloudbackupconfig is None:
            pub_user_message(payload, connection_id,
                             "Es ist keine Backup-Cloud konfiguriert. Bitte Konfiguration speichern "
                             "und erneut versuchen.<br />", MessageType.WARNING)
            return
        result = generateMSALAuthCode(cloudbackupconfig.config)
        pub_user_message(payload, connection_id, result["message"], result["MessageType"])

    # ToDo: move to module commands if implemented
    def retrieveMSALTokens(self, connection_id: str, payload: dict) -> None:
        """ holt die Tokens für MSAL (Microsoft Authentication Library) um Onedrive Backup zu ermöglichen
        """
        cloudbackupconfig = SubData.system_data["system"].backup_cloud
        if cloudbackupconfig is None:
            pub_user_message(payload, connection_id,
                             "Es ist keine Backup-Cloud konfiguriert. Bitte Konfiguration speichern "
                             "und erneut versuchen.<br />", MessageType.WARNING)
            return
        result = retrieveMSALTokens(cloudbackupconfig.config)
        pub_user_message(payload, connection_id, result["message"], result["MessageType"])

    def factoryReset(self, connection_id: str, payload: dict) -> None:
        Path(Path(__file__).resolve().parents[2] / 'data' / 'restore' / 'factory_reset').touch()
        pub_user_message(payload, connection_id,
                         ("Zurücksetzen auf Werkseinstellungen wurde vorbereitet."
                          " openWB wird jetzt zum Abschluss neu gestartet."),
                         MessageType.INFO)
        self.systemReboot(connection_id, payload)

    def dataMigration(self, connection_id: str, payload: dict) -> None:
        pub_user_message(payload, connection_id, "Datenübernahme gestartet.", MessageType.INFO)
        migrate_data = MigrateData(payload["data"])
        migrate_data.validate_ids()
        migrate_data.migrate()
        pub_user_message(payload, connection_id, "Datenübernahme abgeschlossen.", MessageType.SUCCESS)

    def removeCloudBridge(self, connection_id: str, payload: dict):
        received_id = ProcessBrokerBranch("system/mqtt/bridge/").get_cloud_id()
        if received_id:
            Pub().pub("openWB/set/command/removeMqttBridge/todo", {
                "command": "removeMqttBridge",
                "data": {
                    "bridge": int(received_id[0])
                }
            })


class ErrorHandlingContext:
    def __init__(self, payload: dict, connection_id: str):
        self.payload = payload
        self.connection_id = connection_id

    def __enter__(self):
        return None

    def __exit__(self, exception_type, exception, exception_traceback) -> bool:
        if isinstance(exception, Exception):
            pub_user_message(self.payload, self.connection_id,
                             f'Es ist ein interner Fehler aufgetreten: {exception}', MessageType.ERROR)
            log.error({traceback.format_exc()})
            return True
        elif isinstance(exception, subprocess.CalledProcessError):
            log.debug(exception.stdout)
            pub_user_message(self.payload, self.connection_id,
                             f'Fehler-Status: {exception.returncode}<br />Meldung: {exception.stderr}',
                             MessageType.ERROR)
            return True
        else:
            return False


class CompleteCommandContext:
    def __init__(self, event_command_completed: threading.Event):
        self.event_command_completed = event_command_completed

    def __enter__(self):
        """Beim Aufruf der Methode wird auf das Setzen des Events gewartet und dann zurückgesetzt."""
        self.event_command_completed.wait()
        self.event_command_completed.clear()
        return None

    def __exit__(self, exception_type, exception, exception_traceback) -> bool:
        """ Als letztes Topic wird command_completed gesendet. Wenn dies in der subdata empfangen wird, wird das
        Event gesetzt. Der nächste Befehl wartet in der Enter-Methode auf das Setzen des Events."""
        Pub().pub("openWB/set/command/command_completed", True)
        return True


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

    def check_mqtt_bridge_exists(self, name: str) -> bool:
        try:
            self.name = name
            self.mqtt_bridge_exists = False
            InternalBrokerClient("processBrokerBranch", self.on_connect,
                                 self.__on_message_mqtt_bridge_exists).start_finite_loop()
            return self.mqtt_bridge_exists
        except Exception:
            log.exception("Fehler im Command-Modul")
            return self.mqtt_bridge_exists

    def get_cloud_id(self):
        try:
            self.ids = []
            InternalBrokerClient("processBrokerBranch", self.on_connect, self.__on_message_cloud_id).start_finite_loop()
            return self.ids
        except Exception:
            log.exception("Fehler im Command-Modul")
            return []

    def on_connect(self, client, userdata, flags, rc):
        """ connect to broker and subscribe to set topics
        """
        client.subscribe(f'openWB/{self.topic_str}#', 2)
        client.subscribe(f'openWB/set/{self.topic_str}#', 2)

    def __on_message_rm(self, client, userdata, msg):
        try:
            if decode_payload(msg.payload) != '':
                log.debug(f'Gelöschtes Topic: {msg.topic}')
                Pub().pub(msg.topic, "")
                if "openWB/system/device/" in msg.topic and "component" in msg.topic and "config" in msg.topic:
                    payload = decode_payload(msg.payload)
                    topic = type_to_topic_mapping(payload["type"])
                    data.data.counter_all_data.hierarchy_remove_item(payload["id"])
                    Pub().pub("openWB/set/counter/get/hierarchy", data.data.counter_all_data.data.get.hierarchy)
                    client.subscribe(f'openWB/{topic}/{payload["id"]}/#', 2)
                elif re.search("openWB/chargepoint/[0-9]+/config$", msg.topic) is not None:
                    payload = decode_payload(msg.payload)
                    if payload["type"] == "external_openwb":
                        pub_single(
                            f'openWB/set/internal_chargepoint/{payload["configuration"]["duo_num"]}/data/parent_cp',
                            None,
                            hostname=payload["configuration"]["ip_address"])
                elif re.search("openWB/chargepoint/template/[0-9]+$", msg.topic) is not None:
                    for cp in SubData.cp_data.values():
                        if cp.chargepoint.data.config.template == int(msg.topic.split("/")[-1]):
                            pub_single(f'openWB/set/chargepoint/{cp.chargepoint.num}/config/template', 0)
                elif re.search("openWB/vehicle/template/charge_template/[0-9]+$", msg.topic) is not None:
                    for vehicle in SubData.ev_data.values():
                        if vehicle.data.charge_template == int(msg.topic.split("/")[-1]):
                            pub_single(f'openWB/set/vehicle/{vehicle.num}/charge_template', 0)
                elif re.search("openWB/vehicle/template/ev_template/[0-9]+$", msg.topic) is not None:
                    for vehicle in SubData.ev_data.values():
                        if vehicle.data.ev_template == int(msg.topic.split("/")[-1]):
                            pub_single(f'openWB/set/vehicle/{vehicle.num}/ev_template', 0)
        except Exception:
            log.exception("Fehler in ProcessBrokerBranch")

    def __on_message_max_id(self, client, userdata, msg):
        try:
            self.received_topics.append(msg.topic)
        except Exception:
            log.exception("Fehler in ProcessBrokerBranch")

    def __get_payload(self, client, userdata, msg):
        try:
            self.payload = msg.payload
        except Exception:
            log.exception("Fehler in ProcessBrokerBranch")

    def __on_message_mqtt_bridge_exists(self, client, userdata, msg):
        try:
            if decode_payload(msg.payload)["name"] == self.name:
                self.mqtt_bridge_exists = True
        except Exception:
            log.exception("Fehler in ProcessBrokerBranch")

    def __on_message_cloud_id(self, client, userdata, msg):
        try:
            if decode_payload(msg.payload)['remote']['is_openwb_cloud']:
                id = msg.topic.replace("openWB/"+self.topic_str, "")
                self.ids.append(id)
        except Exception:
            log.exception("Fehler in ProcessBrokerBranch")
