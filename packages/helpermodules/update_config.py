from dataclasses import asdict
import glob
import json
import logging
from pathlib import Path
import re
import subprocess
import time
from typing import List
from paho.mqtt.client import Client as MqttClient, MQTTMessage

from helpermodules.broker import InternalBrokerClient
from helpermodules.pub import Pub
from helpermodules.utils.topic_parser import decode_payload, get_index, get_second_index
from helpermodules import measurement_log
from control import chargepoint, counter_all
from control import ev

log = logging.getLogger(__name__)


class UpdateConfig:
    DATASTORE_VERSION = 8
    valid_topic = ["^openWB/bat/config/configured$",
                   "^openWB/bat/set/charging_power_left$",
                   "^openWB/bat/set/switch_on_soc_reached$",
                   "^openWB/bat/get/soc$",
                   "^openWB/bat/get/power$",
                   "^openWB/bat/get/imported$",
                   "^openWB/bat/get/exported$",
                   "^openWB/bat/get/daily_exported$",
                   "^openWB/bat/get/daily_imported$",
                   "^openWB/bat/[0-9]+/get/soc$",
                   "^openWB/bat/[0-9]+/get/power$",
                   "^openWB/bat/[0-9]+/get/imported$",
                   "^openWB/bat/[0-9]+/get/exported$",
                   "^openWB/bat/[0-9]+/get/daily_exported$",
                   "^openWB/bat/[0-9]+/get/daily_imported$",
                   "^openWB/bat/[0-9]+/get/fault_state$",
                   "^openWB/bat/[0-9]+/get/fault_str$",

                   "^openWB/chargepoint/get/power$",
                   "^openWB/chargepoint/get/exported$",
                   "^openWB/chargepoint/get/imported$",
                   "^openWB/chargepoint/get/daily_exported$",
                   "^openWB/chargepoint/get/daily_imported$",
                   "^openWB/chargepoint/template/[0-9]+$",
                   "^openWB/chargepoint/template/[0-9]+/autolock/[0-9]+$",
                   "^openWB/chargepoint/[0-9]+/config$",
                   "^openWB/chargepoint/[0-9]+/get/charge_state$",
                   "^openWB/chargepoint/[0-9]+/get/currents$",
                   "^openWB/chargepoint/[0-9]+/get/fault_state$",
                   "^openWB/chargepoint/[0-9]+/get/fault_str$",
                   "^openWB/chargepoint/[0-9]+/get/plug_state$",
                   "^openWB/chargepoint/[0-9]+/get/phases_in_use$",
                   "^openWB/chargepoint/[0-9]+/get/exported$",
                   "^openWB/chargepoint/[0-9]+/get/imported$",
                   "^openWB/chargepoint/[0-9]+/get/daily_exported$",
                   "^openWB/chargepoint/[0-9]+/get/daily_imported$",
                   "^openWB/chargepoint/[0-9]+/get/power$",
                   "^openWB/chargepoint/[0-9]+/get/voltages$",
                   "^openWB/chargepoint/[0-9]+/get/state_str$",
                   "^openWB/chargepoint/[0-9]+/get/connected_vehicle/soc_config$",
                   "^openWB/chargepoint/[0-9]+/get/connected_vehicle/soc$",
                   "^openWB/chargepoint/[0-9]+/get/connected_vehicle/info$",
                   "^openWB/chargepoint/[0-9]+/get/connected_vehicle/config$",
                   "^openWB/chargepoint/[0-9]+/get/rfid$",
                   "^openWB/chargepoint/[0-9]+/get/rfid_timestamp$",
                   "^openWB/chargepoint/[0-9]+/set/charging_ev$",
                   "^openWB/chargepoint/[0-9]+/set/current$",
                   "^openWB/chargepoint/[0-9]+/set/energy_to_charge$",
                   "^openWB/chargepoint/[0-9]+/set/manual_lock$",
                   "^openWB/chargepoint/[0-9]+/set/plug_time$",
                   "^openWB/chargepoint/[0-9]+/set/rfid$",
                   "^openWB/chargepoint/[0-9]+/set/change_ev_permitted$",
                   "^openWB/chargepoint/[0-9]+/set/log$",
                   "^openWB/chargepoint/[0-9]+/set/phases_to_use$",
                   "^openWB/chargepoint/[0-9]+/set/charging_ev_prev$",

                   "^openWB/command/max_id/autolock_plan$",
                   "^openWB/command/max_id/charge_template$",
                   "^openWB/command/max_id/charge_template_scheduled_plan$",
                   "^openWB/command/max_id/charge_template_time_charging_plan$",
                   "^openWB/command/max_id/chargepoint_template$",
                   "^openWB/command/max_id/device$",
                   "^openWB/command/max_id/ev_template$",
                   "^openWB/command/max_id/hierarchy$",
                   "^openWB/command/max_id/mqtt_bridge$",
                   "^openWB/command/max_id/vehicle$",
                   "^openWB/command/[A-Za-z0-9_]+/error$",
                   "^openWB/command/todo$",

                   "^openWB/counter/config/reserve_for_not_charging$",
                   "^openWB/counter/get/hierarchy$",
                   "^openWB/counter/set/invalid_home_consumption$",
                   "^openWB/counter/set/home_consumption$",
                   "^openWB/counter/set/daily_yield_home_consumption$",
                   "^openWB/counter/[0-9]+/get/voltages$",
                   "^openWB/counter/[0-9]+/get/power$",
                   "^openWB/counter/[0-9]+/get/currents$",
                   "^openWB/counter/[0-9]+/get/powers$",
                   "^openWB/counter/[0-9]+/get/power_factors$",
                   "^openWB/counter/[0-9]+/get/fault_state$",
                   "^openWB/counter/[0-9]+/get/fault_str$",
                   "^openWB/counter/[0-9]+/get/frequency$",
                   "^openWB/counter/[0-9]+/get/daily_exported$",
                   "^openWB/counter/[0-9]+/get/daily_imported$",
                   "^openWB/counter/[0-9]+/get/imported$",
                   "^openWB/counter/[0-9]+/get/exported$",
                   "^openWB/counter/[0-9]+/set/consumption_left$",
                   "^openWB/counter/[0-9]+/set/state_str$",
                   "^openWB/counter/[0-9]+/config/max_currents$",
                   "^openWB/counter/[0-9]+/config/max_total_power$",

                   "^openWB/general/extern$",
                   "^openWB/general/extern_display_mode$",
                   "^openWB/general/control_interval$",
                   "^openWB/general/external_buttons_hw$",
                   "^openWB/general/grid_protection_configured$",
                   "^openWB/general/grid_protection_active$",
                   "^openWB/general/mqtt_bridge$",
                   "^openWB/general/grid_protection_timestamp$",
                   "^openWB/general/grid_protection_random_stop$",
                   "^openWB/general/price_kwh$",
                   "^openWB/general/range_unit$",
                   "^openWB/general/notifications/selected$",
                   "^openWB/general/notifications/configuration$",
                   "^openWB/general/notifications/start_charging$",
                   "^openWB/general/notifications/stop_charging$",
                   "^openWB/general/notifications/plug$",
                   "^openWB/general/notifications/smart_home$",
                   "^openWB/general/ripple_control_receiver/configured$",
                   "^openWB/general/ripple_control_receiver/r1_active$",
                   "^openWB/general/ripple_control_receiver/r2_active$",
                   "^openWB/general/chargemode_config/unbalanced_load_limit$",
                   "^openWB/general/chargemode_config/unbalanced_load$",
                   "^openWB/general/chargemode_config/pv_charging/feed_in_yield$",
                   "^openWB/general/chargemode_config/pv_charging/switch_on_threshold$",
                   "^openWB/general/chargemode_config/pv_charging/switch_on_delay$",
                   "^openWB/general/chargemode_config/pv_charging/switch_off_threshold$",
                   "^openWB/general/chargemode_config/pv_charging/switch_off_delay$",
                   "^openWB/general/chargemode_config/pv_charging/phase_switch_delay$",
                   "^openWB/general/chargemode_config/pv_charging/control_range$",
                   "^openWB/general/chargemode_config/pv_charging/phases_to_use$",
                   "^openWB/general/chargemode_config/pv_charging/bat_prio$",
                   "^openWB/general/chargemode_config/pv_charging/switch_on_soc$",
                   "^openWB/general/chargemode_config/pv_charging/switch_off_soc$",
                   "^openWB/general/chargemode_config/pv_charging/rundown_soc$",
                   "^openWB/general/chargemode_config/pv_charging/rundown_power$",
                   "^openWB/general/chargemode_config/pv_charging/charging_power_reserve$",
                   "^openWB/general/chargemode_config/scheduled_charging/phases_to_use$",
                   "^openWB/general/chargemode_config/instant_charging/phases_to_use$",
                   "^openWB/general/chargemode_config/standby/phases_to_use$",
                   "^openWB/general/chargemode_config/stop/phases_to_use$",
                   "^openWB/general/chargemode_config/time_charging/phases_to_use$",

                   "^openWB/graph/config/duration$",
                   "^openWB/graph/alllivevaluesJson",
                   "^openWB/graph/lastlivevaluesJson$",

                   "^openWB/set/log/request",
                   "^openWB/set/log/data",

                   "^openWB/optional/et/active$",
                   "^openWB/optional/et/get/price_list$",
                   "^openWB/optional/et/get/price$",
                   "^openWB/optional/et/get/source$",
                   "^openWB/optional/et/config/max_price$",
                   "^openWB/optional/et/config/provider$",
                   "^openWB/optional/int_display/active$",
                   "^openWB/optional/int_display/on_if_plugged_in$",
                   "^openWB/optional/int_display/pin_active$",
                   "^openWB/optional/int_display/pin_code$",
                   "^openWB/optional/int_display/standby$",
                   "^openWB/optional/int_display/theme$",
                   "^openWB/optional/led/active$",
                   "^openWB/optional/rfid/active$",

                   "^openWB/pv/config/configured$",
                   "^openWB/pv/get/exported$",
                   "^openWB/pv/get/power$",
                   "^openWB/pv/get/daily_exported$",
                   "^openWB/pv/get/monthly_exported$",
                   "^openWB/pv/get/yearly_exported$",
                   "^openWB/pv/[0-9]+/config/max_ac_out$",
                   "^openWB/pv/[0-9]+/get/exported$",
                   "^openWB/pv/[0-9]+/get/power$",
                   "^openWB/pv/[0-9]+/get/currents$",
                   "^openWB/pv/[0-9]+/get/energy$",
                   "^openWB/pv/[0-9]+/get/daily_exported$",
                   "^openWB/pv/[0-9]+/get/monthly_exported$",
                   "^openWB/pv/[0-9]+/get/yearly_exported$",
                   "^openWB/pv/[0-9]+/get/fault_state$",
                   "^openWB/pv/[0-9]+/get/fault_str$",

                   "^openWB/vehicle/template/ev_template/[0-9]+$",
                   "^openWB/vehicle/template/charge_template/[0-9]+/time_charging/plans/[0-9]+$",
                   "^openWB/vehicle/template/charge_template/[0-9]+/chargemode/scheduled_charging/plans/[0-9]+$",
                   "^openWB/vehicle/template/charge_template/[0-9]+",
                   "^openWB/vehicle/[0-9]+/charge_template$",
                   "^openWB/vehicle/[0-9]+/ev_template$",
                   "^openWB/vehicle/[0-9]+/name$",
                   "^openWB/vehicle/[0-9]+/soc_module/config$",
                   "^openWB/vehicle/[0-9]+/tag_id$",
                   "^openWB/vehicle/[0-9]+/get/fault_state$",
                   "^openWB/vehicle/[0-9]+/get/fault_str$",
                   "^openWB/vehicle/[0-9]+/get/force_soc_update$",
                   "^openWB/vehicle/[0-9]+/get/range$",
                   "^openWB/vehicle/[0-9]+/get/soc$",
                   "^openWB/vehicle/[0-9]+/get/soc_timestamp$",
                   "^openWB/vehicle/[0-9]+/match_ev/selected$",
                   "^openWB/vehicle/[0-9]+/match_ev/tag_id$",
                   "^openWB/vehicle/[0-9]+/control_parameter/submode$",
                   "^openWB/vehicle/[0-9]+/control_parameter/chargemode$",
                   "^openWB/vehicle/[0-9]+/control_parameter/current_plan$",
                   "^openWB/vehicle/[0-9]+/control_parameter/imported_at_plan_start$",
                   "^openWB/vehicle/[0-9]+/control_parameter/prio$",
                   "^openWB/vehicle/[0-9]+/control_parameter/required_current$",
                   "^openWB/vehicle/[0-9]+/control_parameter/timestamp_auto_phase_switch$",
                   "^openWB/vehicle/[0-9]+/control_parameter/timestamp_perform_phase_switch$",
                   "^openWB/vehicle/[0-9]+/control_parameter/timestamp_switch_on_off$",
                   "^openWB/vehicle/[0-9]+/control_parameter/used_amount_instant_charging$",
                   "^openWB/vehicle/[0-9]+/control_parameter/phases$",
                   "^openWB/vehicle/[0-9]+/control_parameter/state$",
                   "^openWB/vehicle/[0-9]+/set/ev_template$",
                   "^openWB/vehicle/[0-9]+/set/soc_error_counter$",

                   "^openWB/system/boot_done$",
                   "^openWB/system/dataprotection_acknowledged$",
                   "^openWB/system/debug_level$",
                   "^openWB/system/lastlivevaluesJson$",
                   "^openWB/system/ip_address$",
                   "^openWB/system/version$",
                   "^openWB/system/release_train$",
                   "^openWB/system/update_in_progress$",
                   "^openWB/system/device/[0-9]+/config$",
                   "^openWB/system/device/[0-9]+/component/[0-9]+/config$",
                   "^openWB/system/device/[0-9]+/component/[0-9]+/simulation$",
                   "^openWB/system/device/[0-9]+/component/[0-9]+/simulation/timestamp_present$",
                   "^openWB/system/device/[0-9]+/component/[0-9]+/simulation/power_present$",
                   "^openWB/system/device/[0-9]+/component/[0-9]+/simulation/present_imported$",
                   "^openWB/system/device/[0-9]+/component/[0-9]+/simulation/present_exported$",
                   "^openWB/system/device/module_update_completed$",
                   "^openWB/system/configurable/soc_modules$",
                   "^openWB/system/configurable/devices_components$",
                   "^openWB/system/configurable/chargepoints$",
                   "^openWB/system/mqtt/bridge/[0-9]+$",
                   "^openWB/system/current_branch",
                   "^openWB/system/current_commit",
                   "^openWB/system/available_branches",
                   "^openWB/system/current_branch_commit",
                   "^openWB/system/current_missing_commits",
                   "^openWB/system/datastore_version"
                   ]
    default_topic = (
        ("openWB/chargepoint/get/power", 0),
        ("openWB/chargepoint/template/0", chargepoint.get_chargepoint_template_default()),
        ("openWB/counter/get/hierarchy", []),
        ("openWB/counter/config/reserve_for_not_charging", counter_all.Config().reserve_for_not_charging),
        ("openWB/vehicle/0/name", ev.EvData().name),
        ("openWB/vehicle/0/charge_template", ev.Ev(0).charge_template.ct_num),
        ("openWB/vehicle/0/soc_module/config", {"type": None, "configuration": {}}),
        ("openWB/vehicle/0/ev_template", ev.Ev(0).ev_template.et_num),
        ("openWB/vehicle/0/tag_id", ev.Ev(0).data.tag_id),
        ("openWB/vehicle/0/get/soc", ev.Ev(0).data.get.soc),
        ("openWB/vehicle/template/ev_template/0", asdict(ev.EvTemplateData())),
        ("openWB/vehicle/template/charge_template/0", ev.get_charge_template_default()),
        ("openWB/general/chargemode_config/instant_charging/phases_to_use", 1),
        ("openWB/general/chargemode_config/pv_charging/bat_prio", 1),
        ("openWB/general/chargemode_config/pv_charging/switch_on_soc", 60),
        ("openWB/general/chargemode_config/pv_charging/switch_off_soc", 40),
        ("openWB/general/chargemode_config/pv_charging/rundown_power", 1000),
        ("openWB/general/chargemode_config/pv_charging/rundown_soc", 50),
        ("openWB/general/chargemode_config/pv_charging/charging_power_reserve", 200),
        ("openWB/general/chargemode_config/pv_charging/control_range", [0, 230]),
        ("openWB/general/chargemode_config/pv_charging/switch_off_threshold", 50),
        ("openWB/general/chargemode_config/pv_charging/switch_off_delay", 60),
        ("openWB/general/chargemode_config/pv_charging/switch_on_delay", 30),
        ("openWB/general/chargemode_config/pv_charging/switch_on_threshold", 1500),
        ("openWB/general/chargemode_config/pv_charging/feed_in_yield", 15000),
        ("openWB/general/chargemode_config/pv_charging/phase_switch_delay", 7),
        ("openWB/general/chargemode_config/pv_charging/phases_to_use", 1),
        ("openWB/general/chargemode_config/scheduled_charging/phases_to_use", 0),
        ("openWB/general/chargemode_config/standby/phases_to_use", 1),
        ("openWB/general/chargemode_config/stop/phases_to_use", 1),
        ("openWB/general/chargemode_config/time_charging/phases_to_use", 1),
        ("openWB/general/chargemode_config/unbalanced_load", False),
        ("openWB/general/chargemode_config/unbalanced_load_limit", 18),
        ("openWB/general/control_interval", 10),
        ("openWB/general/extern", False),
        ("openWB/general/extern_display_mode", "local"),
        ("openWB/general/external_buttons_hw", False),
        ("openWB/general/grid_protection_configured", True),
        ("openWB/general/notifications/selected", "none"),
        ("openWB/general/notifications/plug", False),
        ("openWB/general/notifications/start_charging", False),
        ("openWB/general/notifications/stop_charging", False),
        ("openWB/general/notifications/smart_home", False),
        ("openWB/general/notifications/configuration", {}),
        ("openWB/general/price_kwh", 0.3),
        ("openWB/general/range_unit", "km"),
        ("openWB/general/ripple_control_receiver/configured", False),
        ("openWB/graph/config/duration", 120),
        ("openWB/optional/et/active", False),
        ("openWB/optional/et/config/max_price", 0),
        ("openWB/optional/et/config/provider", {}),
        ("openWB/optional/int_display/active", False),
        ("openWB/optional/int_display/on_if_plugged_in", True),
        ("openWB/optional/int_display/pin_active", False),
        ("openWB/optional/int_display/pin_code", "0000"),
        ("openWB/optional/int_display/standby", 60),
        ("openWB/optional/int_display/theme", "cards"),
        ("openWB/optional/led/active", False),
        ("openWB/optional/rfid/active", False),
        ("openWB/system/dataprotection_acknowledged", False),
        ("openWB/system/debug_level", 30),
        ("openWB/system/device/module_update_completed", True),
        ("openWB/system/ip_address", "unknown"),
        ("openWB/system/release_train", "master"))

    def __init__(self) -> None:
        self.all_received_topics = {}

    def update(self):
        log.debug("Broker-Konfiguration aktualisieren")
        InternalBrokerClient("update-config", self.on_connect, self.on_message).start_finite_loop()
        try:
            self.__remove_outdated_topics()
            self._remove_invalid_topics()
            self.__pub_missing_defaults()
            self.__update_version()
            self.__solve_breaking_changes()
        except Exception:
            log.exception("Fehler beim Prüfen des Brokers.")

    def on_connect(self, client: MqttClient, userdata, flags: dict, rc: int):
        """ connect to broker and subscribe to set topics
        """
        client.subscribe("openWB/#", 2)

    def on_message(self, client: MqttClient, userdata, msg: MQTTMessage):
        self.all_received_topics.update({msg.topic: msg.payload})

    def __remove_outdated_topics(self):
        # ungültige Topics entfernen
        # aufpassen mit dynamischen Zweigen! z.B. vehicle/x/...
        for topic in self.all_received_topics.keys():
            for valid_topic in self.valid_topic:
                if re.search(valid_topic, topic) is not None:
                    break
            else:
                Pub().pub(topic, "")
                log.debug("Ungültiges Topic zum Startzeitpunkt: "+str(topic))

    def _remove_invalid_topics(self):
        # remove all charge points without config. This data comes from deleted charge points that are still sent to an
        # invalid CP number.
        for topic in self.all_received_topics.keys():
            if re.search("/chargepoint/[0-9]+/", topic) is not None:
                if f"openWB/chargepoint/{get_index(topic)}/config" not in self.all_received_topics.keys():
                    Pub().pub(topic, "")

    def __pub_missing_defaults(self):
        # zwingend erforderliche Standardwerte setzen
        for topic in self.default_topic:
            if topic[0] not in self.all_received_topics.keys():
                log.debug("Setzte Topic '%s' auf Standardwert '%s'" % (topic[0], str(topic[1])))
                Pub().pub(topic[0].replace("openWB/", "openWB/set/"), topic[1])

    def __update_version(self):
        with open("/var/www/html/openWB/web/version", "r") as f:
            version = f.read().splitlines()[0]
        Pub().pub("openWB/set/system/version", version)

    def __solve_breaking_changes(self) -> None:
        datastore_version = decode_payload(self.all_received_topics.get("openWB/system/datastore_version")) or 0
        for version in range(datastore_version, self.DATASTORE_VERSION):
            try:
                getattr(self, f"upgrade_datastore_{version}")()
            except AttributeError:
                log.error("missing upgrade function! $version$")

    def upgrade_datastore_0(self) -> None:
        # prevent_switch_stop auf zwei Einstellungen prevent_phase_switch und prevent_charge_stop aufteilen
        for topic, payload in self.all_received_topics.items():
            if "openWB/vehicle/template/ev_template/" in topic:
                payload = decode_payload(payload)
                if "prevent_switch_stop" in payload:
                    combined_setting = payload["prevent_switch_stop"]
                    payload.pop("prevent_switch_stop")
                    payload.update({"prevent_charge_stop": combined_setting, "prevent_phase_switch": combined_setting})
                    Pub().pub(topic.replace("openWB/", "openWB/set/"), payload)
        # Alpha2
        # zu konfiguriertem Wechselrichter die maximale Ausgangsleistung hinzufügen
        for topic, payload in self.all_received_topics.items():
            regex = re.search("(openWB/pv/[0-9]+)/get/fault_state", topic)
            if regex is not None:
                module = regex.group(1)
                if f"{module}/config/max_ac_out" not in self.all_received_topics.keys():
                    Pub().pub(
                        f'{module.replace("openWB/", "openWB/set/")}/config/max_ac_out', 0)

        # Alpha 3
        # Summen in Tages- und Monats-Log hinzufügen
        files = glob.glob("/var/www/html/openWB/data/daily_log/*")
        files.extend(glob.glob("/var/www/html/openWB/data/monthly_log/*"))
        for file in files:
            with open(file, "r+") as jsonFile:
                try:
                    content = json.load(jsonFile)
                    if isinstance(content, List):
                        try:
                            new_content = {"entries": content, "totals": measurement_log.get_totals(content)}
                            jsonFile.seek(0)
                            json.dump(new_content, jsonFile)
                            jsonFile.truncate()
                            log.debug(f"Format der Logdatei {file} aktualisiert.")
                        except Exception:
                            log.exception(f"Logfile {file} entspricht nicht dem Dateiformat von Alpha 3.")
                except json.decoder.JSONDecodeError:
                    log.exception(
                        f"Logfile {file} konnte nicht konvertiert werden, da es keine gültigen json-Daten enthält.")
            with open(file, "r+") as jsonFile:
                try:
                    content = json.load(jsonFile)
                    for e in content["entries"]:
                        for module in e["pv"]:
                            if e["pv"][module].get("imported"):
                                e["pv"][module]["exported"] = e["pv"][module]["imported"]
                                e["pv"][module].pop("imported")
                    for entry in content["totals"]["pv"]:
                        if content["totals"]["pv"][entry].get("imported"):
                            content["totals"]["pv"][entry]["exported"] = content["totals"]["pv"][entry]["imported"]
                            content["totals"]["pv"][entry].pop("imported")
                    jsonFile.seek(0)
                    json.dump(content, jsonFile)
                    jsonFile.truncate()
                except Exception:
                    log.exception(f"Logfile {file} konnte nicht konvertiert werden.")

        # prevent_switch_stop auf zwei Einstellungen prevent_phase_switch und prevent_charge_stop aufteilen
        for topic, payload in self.all_received_topics.items():
            if re.search("^openWB/system/device/[0-9]+/config$", topic) is not None:
                payload = decode_payload(payload)
                if payload["type"] == "http":
                    index = get_index(topic)
                    for topic, payload in self.all_received_topics.items():
                        if re.search(f"^openWB/system/device/{index}/component/[0-9]+/config$", topic) is not None:
                            payload = decode_payload(payload)
                            if payload["type"] == "inverter" and "counter_path" in payload["configuration"]:
                                updated_payload = payload
                                updated_payload["configuration"]["exported_path"] = payload[
                                    "configuration"]["counter_path"]
                                updated_payload["configuration"].pop("counter_path")
                                Pub().pub(topic.replace("openWB/", "openWB/set/"), updated_payload)
                elif payload["type"] == "json":
                    index = get_index(topic)
                    for topic, payload in self.all_received_topics.items():
                        if re.search(f"^openWB/system/device/{index}/component/[0-9]+/config$", topic) is not None:
                            payload = decode_payload(payload)
                            if payload["type"] == "inverter" and "jq_counter" in payload["configuration"]:
                                updated_payload = payload
                                updated_payload["configuration"]["jq_exported"] = payload["configuration"]["jq_counter"]
                                updated_payload["configuration"].pop("jq_counter")
                                Pub().pub(topic.replace("openWB/", "openWB/set/"), updated_payload)
                elif payload["type"] == "byd":
                    updated_payload = payload
                    updated_payload["configuration"]["user"] = payload["configuration"]["username"]
                    updated_payload["configuration"].pop("username")
                    Pub().pub(topic.replace("openWB/", "openWB/set/"), updated_payload)
                elif payload["type"] == "good_we":
                    updated_payload = payload
                    updated_payload["configuration"]["modbus_id"] = payload["configuration"]["id"]
                    updated_payload["configuration"].pop("id")
                    Pub().pub(topic.replace("openWB/", "openWB/set/"), updated_payload)
        Pub().pub("openWB/set/system/datastore_version", 1)

    def upgrade_datastore_1(self) -> None:
        def convert_ws_to_wh(value: float) -> float:
            return value / 3600

        def get_decoded_value(name: str) -> float:
            return decode_payload(self.all_received_topics[f"{simulation_topic}/{name}"])
        for topic in self.all_received_topics.keys():
            if re.search("^openWB/system/device/[0-9]+/component/[0-9]+/config$", topic) is not None:
                simulation_topic = (f"openWB/system/device/{get_index(topic)}/component/"
                                    f"{get_second_index(topic)}/simulation")
                if self.all_received_topics.get(f"{simulation_topic}/timestamp_present"):
                    Pub().pub(simulation_topic.replace("openWB/", "openWB/set/"), {
                        "timestamp": float(get_decoded_value("timestamp_present")),
                        "power": get_decoded_value("power_present"),
                        "imported": convert_ws_to_wh(get_decoded_value("present_imported")),
                        "exported": convert_ws_to_wh(get_decoded_value("present_exported"))
                    })
                    Pub().pub(f"{simulation_topic}/timestamp_present", "")
                    Pub().pub(f"{simulation_topic}/power_present", "")
                    Pub().pub(f"{simulation_topic}/present_imported", "")
                    Pub().pub(f"{simulation_topic}/present_exported", "")
        Pub().pub("openWB/set/system/datastore_version", 2)

    def upgrade_datastore_2(self) -> None:
        for topic, payload in self.all_received_topics.items():
            if re.search(
                    "openWB/vehicle/template/charge_template/[0-9]+/chargemode/scheduled_charging/plans/[0-9]+",
                    topic) is not None:
                payload = decode_payload(payload)
                if payload["limit"].get("soc"):
                    updated_payload = payload
                    updated_payload["limit"]["soc_scheduled"] = payload["limit"]["soc"]
                    updated_payload["limit"]["soc_limit"] = payload["limit"]["soc"]
                    updated_payload["limit"].pop("soc")
                    Pub().pub(topic.replace("openWB/", "openWB/set/"), updated_payload)
        Pub().pub("openWB/set/system/datastore_version", 3)

    def upgrade_datastore_3(self) -> None:
        for topic, payload in self.all_received_topics.items():
            if re.search(
                    "openWB/vehicle/template/charge_template/[0-9]+/time_charging/plans/[0-9]+",
                    topic) is not None:
                payload = decode_payload(payload)
                if "limit" not in payload:
                    updated_payload = payload
                    updated_payload["limit"] = {"selected": "soc", "amount": 1000, "soc": 70}
                    Pub().pub(topic.replace("openWB/", "openWB/set/"), updated_payload)
        Pub().pub("openWB/set/system/datastore_version", 4)

    def upgrade_datastore_4(self) -> None:
        moved_file = False
        for path in Path("/etc/mosquitto/conf.d").glob('99-bridge-openwb-*.conf'):
            subprocess.run(["sudo", "mv", str(path), str(path).replace("conf.d", "conf_local.d")])
            moved_file = True
        Pub().pub("openWB/set/system/datastore_version", 5)
        if moved_file:
            time.sleep(1)
            parent_file = Path(__file__).resolve().parents[2]
            subprocess.run([str(parent_file / "runs" / "reboot.sh")])

    def upgrade_datastore_5(self) -> None:
        for topic, payload in self.all_received_topics.items():
            if re.search("openWB/chargepoint/template/[0-9]+", topic) is not None:
                payload = decode_payload(payload)
                if "max_current_single_phase" not in payload:
                    updated_payload = payload
                    updated_payload["max_current_single_phase"] = 32
                    updated_payload["max_current_multi_phases"] = 32
                    Pub().pub(topic.replace("openWB/", "openWB/set/"), updated_payload)
        Pub().pub("openWB/set/system/datastore_version", 6)

    def upgrade_datastore_6(self) -> None:
        for topic, payload in self.all_received_topics.items():
            if re.search("openWB/chargepoint/template/[0-9]+$", topic) is not None:
                payload = decode_payload(payload)
                if "plans" in payload["autolock"]:
                    payload["autolock"].pop("plans")
                    Pub().pub(topic.replace("openWB/", "openWB/set/"), payload)
        Pub().pub("openWB/set/system/datastore_version", 7)

    def upgrade_datastore_7(self) -> None:
        for topic, payload in self.all_received_topics.items():
            if re.search("openWB/vehicle/template/ev_template/[0-9]+$", topic) is not None:
                payload = decode_payload(payload)
                if "keep_charge_active_duration" not in payload:
                    payload["keep_charge_active_duration"] = ev.EvTemplateData().keep_charge_active_duration
                    Pub().pub(topic.replace("openWB/", "openWB/set/"), payload)
        Pub().pub("openWB/set/system/datastore_version", 8)
