import logging
import re
import time
import paho.mqtt.client as mqtt

from helpermodules.pub import Pub
from control import chargepoint
from control import ev

log = logging.getLogger(__name__)


class UpdateConfig:
    valid_topic = ["^openWB/bat/config/configured$",
                   "^openWB/bat/set/charging_power_left$",
                   "^openWB/bat/set/switch_on_soc_reached$",
                   "^openWB/bat/set/hybrid_system_detected$",
                   "^openWB/bat/get/soc$",
                   "^openWB/bat/get/power$",
                   "^openWB/bat/get/imported$",
                   "^openWB/bat/get/exported$",
                   "^openWB/bat/get/daily_yield_export$",
                   "^openWB/bat/get/daily_yield_import$",
                   "^openWB/bat/[0-9]+/get/soc$",
                   "^openWB/bat/[0-9]+/get/power$",
                   "^openWB/bat/[0-9]+/get/imported$",
                   "^openWB/bat/[0-9]+/get/exported$",
                   "^openWB/bat/[0-9]+/get/daily_yield_export$",
                   "^openWB/bat/[0-9]+/get/daily_yield_import$",
                   "^openWB/bat/[0-9]+/get/fault_state$",
                   "^openWB/bat/[0-9]+/get/fault_str$",

                   "^openWB/chargepoint/get/power$",
                   "^openWB/chargepoint/get/counter$",
                   "^openWB/chargepoint/get/daily_yield$",
                   "^openWB/chargepoint/template/0$",
                   "^openWB/chargepoint/template/0/autolock/0$",
                   "^openWB/chargepoint/[0-9]+/config$",
                   "^openWB/chargepoint/[0-9]+/get/charge_state$",
                   "^openWB/chargepoint/[0-9]+/get/currents$",
                   "^openWB/chargepoint/[0-9]+/get/fault_state$",
                   "^openWB/chargepoint/[0-9]+/get/fault_str$",
                   "^openWB/chargepoint/[0-9]+/get/plug_state$",
                   "^openWB/chargepoint/[0-9]+/get/phases_in_use$",
                   "^openWB/chargepoint/[0-9]+/get/counter$",
                   "^openWB/chargepoint/[0-9]+/get/power$",
                   "^openWB/chargepoint/[0-9]+/get/voltages$",
                   "^openWB/chargepoint/[0-9]+/get/state_str$",
                   "^openWB/chargepoint/[0-9]+/get/daily_yield$",
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
                   "^openWB/chargepoint/[0-9]+/set/log/charged_since_mode_switch$",
                   "^openWB/chargepoint/[0-9]+/set/log/charged_since_plugged_counter$",
                   "^openWB/chargepoint/[0-9]+/set/log/chargemode_log_entry$",
                   "^openWB/chargepoint/[0-9]+/set/log/counter_at_mode_switch$",
                   "^openWB/chargepoint/[0-9]+/set/log/counter_at_plugtime$",
                   "^openWB/chargepoint/[0-9]+/set/log/range_charged$",
                   "^openWB/chargepoint/[0-9]+/set/log/timestamp_start_charging$",
                   "^openWB/chargepoint/[0-9]+/set/log/time_charged$",
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
                   "^openWB/counter/[0-9]+/get/daily_yield_export$",
                   "^openWB/counter/[0-9]+/get/daily_yield_import$",
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
                   "^openWB/general/chargemode_config/individual_mode$",
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

                   "^openWB/optional/load_sharing/active$",
                   "^openWB/optional/load_sharing/max_current$",
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
                   "^openWB/pv/set/overhang_power_left$",
                   "^openWB/pv/set/reserved_evu_overhang$",
                   "^openWB/pv/set/released_evu_overhang$",
                   "^openWB/pv/set/available_power$",
                   "^openWB/pv/get/counter$",
                   "^openWB/pv/get/power$",
                   "^openWB/pv/get/daily_yield$",
                   "^openWB/pv/get/monthly_yield$",
                   "^openWB/pv/get/yearly_yield$",
                   "^openWB/pv/[0-9]+/get/counter$",
                   "^openWB/pv/[0-9]+/get/power$",
                   "^openWB/pv/[0-9]+/get/currents$",
                   "^openWB/pv/[0-9]+/get/energy$",
                   "^openWB/pv/[0-9]+/get/daily_yield$",
                   "^openWB/pv/[0-9]+/get/monthly_yield$",
                   "^openWB/pv/[0-9]+/get/yearly_yield$",
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
                   "^openWB/vehicle/[0-9]+/get/range$",
                   "^openWB/vehicle/[0-9]+/get/soc$",
                   "^openWB/vehicle/[0-9]+/get/soc_timestamp$",
                   "^openWB/vehicle/[0-9]+/match_ev/selected$",
                   "^openWB/vehicle/[0-9]+/match_ev/tag_id$",
                   "^openWB/vehicle/[0-9]+/control_parameter/submode$",
                   "^openWB/vehicle/[0-9]+/control_parameter/chargemode$",
                   "^openWB/vehicle/[0-9]+/control_parameter/prio$",
                   "^openWB/vehicle/[0-9]+/control_parameter/required_current$",
                   "^openWB/vehicle/[0-9]+/control_parameter/timestamp_auto_phase_switch$",
                   "^openWB/vehicle/[0-9]+/control_parameter/timestamp_perform_phase_switch$",
                   "^openWB/vehicle/[0-9]+/control_parameter/used_amount$",
                   "^openWB/vehicle/[0-9]+/control_parameter/phases$",
                   "^openWB/vehicle/[0-9]+/set/ev_template$",

                   "^openWB/system/boot_done$",
                   "^openWB/system/dataprotection_acknowledged$",
                   "^openWB/system/debug_level$",
                   "^openWB/system/lastlivevaluesJson$",
                   "^openWB/system/ip_address$",
                   "^openWB/system/release_train$",
                   "^openWB/system/update_in_progress$",
                   "^openWB/system/device/[0-9]+/config$",
                   "^openWB/system/device/[0-9]+/component/[0-9]+/config$",
                   "^openWB/system/device/[0-9]+/component/[0-9]+/simulation/timestamp_present$",
                   "^openWB/system/device/[0-9]+/component/[0-9]+/simulation/power_present$",
                   "^openWB/system/device/[0-9]+/component/[0-9]+/simulation/present_imported$",
                   "^openWB/system/device/[0-9]+/component/[0-9]+/simulation/present_exported$",
                   "^openWB/system/configurable/soc_modules$",
                   "^openWB/system/configurable/devices_components$",
                   "^openWB/system/configurable/chargepoints$",
                   "^openWB/system/mqtt/bridge/[0-9]+$"
                   ]
    default_topic = (
        ("openWB/chargepoint/template/0", chargepoint.get_chargepoint_template_default()),
        ("openWB/counter/get/hierarchy", []),
        ("openWB/vehicle/0/name", ev.get_vehicle_default()["name"]),
        ("openWB/vehicle/0/charge_template", ev.get_vehicle_default()["charge_template"]),
        ("openWB/vehicle/0/soc_module/config", {"type": None, "configuration": {}}),
        ("openWB/vehicle/0/ev_template", ev.get_vehicle_default()["ev_template"]),
        ("openWB/vehicle/0/tag_id", ev.get_vehicle_default()["tag_id"]),
        ("openWB/vehicle/0/get/soc", ev.get_vehicle_default()["get/soc"]),
        ("openWB/vehicle/template/ev_template/0", ev.get_ev_template_default()),
        ("openWB/vehicle/template/charge_template/0", ev.get_charge_template_default()),
        ("openWB/general/chargemode_config/instant_charging/phases_to_use", 1),
        ("openWB/general/chargemode_config/pv_charging/bat_prio", 1),
        ("openWB/general/chargemode_config/pv_charging/switch_on_soc", 60),
        ("openWB/general/chargemode_config/pv_charging/switch_off_soc", 40),
        ("openWB/general/chargemode_config/pv_charging/rundown_power", 1000),
        ("openWB/general/chargemode_config/pv_charging/rundown_soc", 50),
        ("openWB/general/chargemode_config/pv_charging/charging_power_reserve", 200),
        ("openWB/general/chargemode_config/pv_charging/control_range", [0, 230]),
        ("openWB/general/chargemode_config/pv_charging/switch_off_threshold", 5),
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
        ("openWB/general/chargemode_config/individual_mode", True),
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
        ("openWB/optional/load_sharing/active", False),
        ("openWB/optional/load_sharing/max_current", 16),
        ("openWB/optional/rfid/active", False),
        ("openWB/system/dataprotection_acknowledged", False),
        ("openWB/system/debug_level", 30),
        ("openWB/system/ip_address", "unknown"),
        ("openWB/system/release_train", "master"))

    def __init__(self) -> None:
        self.all_received_topics = []

    def update(self):
        log.debug("Broker-Konfiguration aktualisieren")
        mqtt_broker_ip = "localhost"
        client = mqtt.Client("openWB-updateconfig-" + self.getserial())
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.connect(mqtt_broker_ip, 1886)
        client.loop_start()
        time.sleep(2)
        client.loop_stop()

        self.__remove_outdated_topics()
        self.__pub_missing_defaults()
        self.__update_version()

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
        client.subscribe("openWB/#", 2)

    def on_message(self, client, userdata, msg):
        self.all_received_topics.append(msg.topic)

    def __remove_outdated_topics(self):
        # ungültige Topics entfernen
        # aufpassen mit dynamischen Zweigen! z.B. vehicle/x/...
        for topic in self.all_received_topics:
            for valid_topic in self.valid_topic:
                if re.search(valid_topic, topic) is not None:
                    break
            else:
                Pub().pub(topic, "")
                log.debug("Ungültiges Topic zum Startzeitpunkt: "+str(topic))

    def __pub_missing_defaults(self):
        # zwingend erforderliche Standardwerte setzen
        for topic in self.default_topic:
            if topic[0] not in self.all_received_topics:
                log.debug("Setzte Topic '%s' auf Standardwert '%s'" % (topic[0], str(topic[1])))
                Pub().pub(topic[0].replace("openWB/", "openWB/set/"), topic[1])

    def __update_version(self):
        with open("/var/www/html/openWB/web/version", "r") as f:
            version = f.read().splitlines()[0]
        Pub().pub("openWB/set/system/version", version)
