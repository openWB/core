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
import dataclass_utils
from control.chargepoint.chargepoint_template import get_chargepoint_template_default

from helpermodules.broker import InternalBrokerClient
from helpermodules.pub import Pub
from helpermodules.utils.topic_parser import decode_payload, get_index, get_second_index
from helpermodules import measurement_log
from control import counter_all
from control import ev
from modules.common.configurable_vehicle import IntervalConfig
from modules.display_themes.cards.config import CardsDisplayTheme

log = logging.getLogger(__name__)


class UpdateConfig:
    DATASTORE_VERSION = 17
    valid_topic = [
        "^openWB/bat/config/configured$",
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
        "^openWB/counter/set/disengageable_smarthome_power$",
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
        "^openWB/general/chargemode_config/time_charging/phases_to_use$",

        "^openWB/graph/config/duration$",
        "^openWB/graph/alllivevaluesJson",
        "^openWB/graph/lastlivevaluesJson$",

        "^openWB/internal_chargepoint/global_data$",
        "^openWB/internal_chargepoint/global_config$",
        "^openWB/internal_chargepoint/[0-1]/data/cp_interruption_duration$",
        "^openWB/internal_chargepoint/[0-1]/data/set_current$",
        "^openWB/internal_chargepoint/[0-1]/data/phases_to_use$",
        "^openWB/internal_chargepoint/[0-1]/data/parent_cp$",

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
        "^openWB/optional/int_display/rotation$",
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
        "^openWB/vehicle/[0-9]+/soc_module/interval_config$",
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

        "^openWB/LegacySmartHome/config/get/logLevel$",
        "^openWB/LegacySmartHome/config/get/maxBatteryPower$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_actor$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_acthortype$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_acthorpower$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_ausschaltschwelle$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_ausschalturl$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_ausschaltverzoegerung$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_configured$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_canSwitch$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_einschalturl$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_chan$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_dacport$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_deactivateper$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_deactivateWhileEvCharging$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_differentMeasurement$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_einschaltschwelle$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_einschaltverzoegerung$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_endTime$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_finishTime$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_homeConsumtion$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_idmnav$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_ip$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_lambdaueb$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_leistungurl$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_manual_control$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_manwatt$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_maxeinschaltdauer$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_mindayeinschaltdauer$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_mineinschaltdauer$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_measchan$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_measureavmusername$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_measureavmpassword$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_measureavmactor$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_measureid$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_measureip$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_measuresmaage$"
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_measuresmaser$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_measurePortSdm$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_measureshauth$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_measureshusername$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_measureshpassword$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_measureType$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_measureurl$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_measureurlc$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_measurejsonurl$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_measurejsonpower$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_measurejsoncounter$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_name$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_nxdacxxtype$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_nxdacxxueb$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_nonewatt$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_offTime$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_onTime$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_onuntilTime$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_password$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_pbip$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_pbtype$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_setauto$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_shusername$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_shpassword$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_shauth$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_startTime$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_startupDetection$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_standbyPower$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_standbyDuration$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_startupMulDetection$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_stateurl$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_speichersocbeforestart$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_speichersocbeforestop$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_temperatur_configured$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_type$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_updatesec$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_username$",
        "^openWB/LegacySmartHome/config/set/Devices/[0-9]+/mode$",
        "^openWB/LegacySmartHome/Devices/[0-9]+/WHImported_temp$",
        "^openWB/LegacySmartHome/Devices/[0-9]+/RunningTimeToday$",
        "^openWB/LegacySmartHome/Devices/[0-9]+/oncountnor$",
        "^openWB/LegacySmartHome/Devices/[0-9]+/OnCntStandby$",
        "^openWB/LegacySmartHome/Devices/[1-2]+/TemperatureSensor[0-2]$",

        "^openWB/system/boot_done$",
        "^openWB/system/backup_cloud/config$",
        "^openWB/system/dataprotection_acknowledged$",
        "^openWB/system/usage_terms_acknowledged$",
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
        "^openWB/system/configurable/backup_clouds$",
        "^openWB/system/configurable/chargepoints$",
        "^openWB/system/configurable/chargepoints_internal$",
        "^openWB/system/configurable/devices_components$",
        "^openWB/system/configurable/display_themes$",
        "^openWB/system/configurable/soc_modules$",
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
        ("openWB/chargepoint/template/0", get_chargepoint_template_default()),
        ("openWB/counter/get/hierarchy", []),
        ("openWB/counter/config/reserve_for_not_charging", counter_all.Config().reserve_for_not_charging),
        ("openWB/vehicle/0/name", ev.EvData().name),
        ("openWB/vehicle/0/charge_template", ev.Ev(0).charge_template.ct_num),
        ("openWB/vehicle/0/soc_module/config", {"type": None, "configuration": {}}),
        ("openWB/vehicle/0/soc_module/interval_config", dataclass_utils.asdict(IntervalConfig())),
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
        ("openWB/optional/int_display/rotation", 180),
        ("openWB/optional/int_display/theme", dataclass_utils.asdict(CardsDisplayTheme())),
        ("openWB/optional/led/active", False),
        ("openWB/optional/rfid/active", False),
        ("openWB/system/backup_cloud/config", {"type": None, "configuration": {}}),
        ("openWB/system/dataprotection_acknowledged", False),
        ("openWB/system/usage_terms_acknowledged", False),
        ("openWB/system/debug_level", 30),
        ("openWB/system/device/module_update_completed", True),
        ("openWB/system/ip_address", "unknown"),
        ("openWB/system/release_train", "master"),
    )
    invalid_topic = (
        # Tuple: (Regex, callable)
        # "callable" must resolve to True if topic has to be deleted
        # "callable" parameters:
        # topic: current topic to validate
        # payload: current payload to validate if needed
        # received_topics: dict of all received topics if needed
        (
            "/chargepoint/[0-9]+/",
            lambda topic, payload, received_topics:
            f"openWB/chargepoint/{get_index(topic)}/config" not in received_topics.keys()
        ),
        ("/int_display/theme$", lambda topic, payload, received_topics: isinstance(decode_payload(payload), str))
    )

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
        # deleting list items while in iteration throws runtime error, so we collect all topics to delete
        topics_to_delete = []
        for topic, payload in self.all_received_topics.items():
            for invalid_topic_regex, invalid_topic_check in self.invalid_topic:
                if (re.search(invalid_topic_regex, topic) is not None and
                        invalid_topic_check(topic, payload, self.all_received_topics)):
                    log.debug(f"Ungültiges Topic '{topic}': {str(payload)}")
                    topics_to_delete.append(topic)
        # delete topics to allow setting new defaults afterwards
        for topic in topics_to_delete:
            Pub().pub(topic, "")
            del self.all_received_topics[topic]

    def __pub_missing_defaults(self):
        # zwingend erforderliche Standardwerte setzen
        for topic, default_payload in self.default_topic:
            if topic not in self.all_received_topics.keys():
                log.debug(f"Setzte Topic '{topic}' auf Standardwert '{str(default_payload)}'")
                Pub().pub(topic.replace("openWB/", "openWB/set/"), default_payload)

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
                log.error(f"missing upgrade function! {version}")

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

    def upgrade_datastore_8(self) -> None:
        for topic, payload in self.all_received_topics.items():
            if re.search("openWB/chargepoint/[0-9]+/config$", topic) is not None:
                payload = decode_payload(payload)
                if "connection_module" in payload:
                    updated_payload = payload
                    try:
                        updated_payload["configuration"] = payload["connection_module"]["configuration"]
                    except KeyError:
                        updated_payload["configuration"] = {}
                    updated_payload.pop("connection_module")
                    updated_payload.pop("power_module")
                    Pub().pub(topic.replace("openWB/", "openWB/set/"), payload)
        Pub().pub("openWB/set/system/datastore_version", 9)

    def upgrade_datastore_9(self) -> None:
        for topic, payload in self.all_received_topics.items():
            if re.search("^openWB/system/mqtt/bridge/[0-9]+$", topic) is not None:
                payload = decode_payload(payload)
                if payload["name"] == "openWBCloud" and "access" not in payload:
                    payload["access"] = {"partner": False}
                    log.debug("cloud bridge configuration upgraded")
                    Pub().pub(topic, payload)
        Pub().pub("openWB/system/datastore_version", 10)

    def upgrade_datastore_10(self) -> None:
        for topic, payload in self.all_received_topics.items():
            if re.search("openWB/vehicle/template/ev_template/[0-9]+$", topic) is not None:
                payload = decode_payload(payload)
                updated_payload = payload
                updated_payload["battery_capacity"] = payload["battery_capacity"] * 1000
                updated_payload["average_consump"] = payload["average_consump"] * 1000
                Pub().pub(topic, updated_payload)
        Pub().pub("openWB/system/datastore_version", 11)

    def upgrade_datastore_11(self) -> None:
        for topic, payload in self.all_received_topics.items():
            if re.search("openWB/chargepoint/[0-9]+/config$", topic) is not None:
                payload = decode_payload(payload)
                if payload["type"] == "openwb_series2_satellit":
                    if "duo_num" not in payload["configuration"]:
                        payload["configuration"].update({"duo_num": 0})
                    Pub().pub(topic.replace("openWB/", "openWB/set/"), payload)
        Pub().pub("openWB/set/system/datastore_version", 12)

    def upgrade_datastore_12(self) -> None:
        for topic, payload in self.all_received_topics.items():
            if re.search("openWB/vehicle/[0-9]+/soc_module/config", topic) is not None:
                payload = decode_payload(payload)
                index = get_index(topic)
                Pub().pub(f"openWB/set/vehicle/{index}/soc_module/interval_config",
                          dataclass_utils.asdict(IntervalConfig()))
        Pub().pub("openWB/system/datastore_version", 13)

    def upgrade_datastore_13(self) -> None:
        for topic, payload in self.all_received_topics.items():
            if re.search("openWB/chargepoint/[0-9]+/config$", topic) is not None:
                updated_payload = decode_payload(payload)
                payload = decode_payload(payload)
                if payload["type"] == "internal_openwb" or payload["type"] == "external_openwb":
                    updated_payload["configuration"]["duo_num"] = payload["configuration"]["duo_num"] - 1
                    Pub().pub(topic.replace("openWB/", "openWB/set/"), updated_payload)
        Pub().pub("openWB/set/system/datastore_version", 14)

    def upgrade_datastore_14(self) -> None:
        for topic, payload in self.all_received_topics.items():
            if re.search("openWB/system/device/[0-9]+/config", topic) is not None:
                payload = decode_payload(payload)
                if payload["type"] == "solar_watt":
                    payload["configuration"]["ip_address"] = payload["configuration"]["ip_adress"]
                    payload.configuration.pop("ip_adress")
                Pub().pub(topic.replace("openWB/", "openWB/set/"), payload)
        Pub().pub("openWB/system/datastore_version", 15)

    def upgrade_datastore_15(self) -> None:
        files = glob.glob("/var/www/html/openWB/data/daily_log/*")
        files.extend(glob.glob("/var/www/html/openWB/data/monthly_log/*"))
        for file in files:
            with open(file, "r+") as jsonFile:
                try:
                    content = json.load(jsonFile)
                    for e in content["entries"]:
                        e.update({"sh": {}})
                    content["totals"].update({"sh": {}})
                    content["names"] = measurement_log.get_names(content["totals"], {})
                    jsonFile.seek(0)
                    json.dump(content, jsonFile)
                    jsonFile.truncate()
                    log.debug(f"Format der Logdatei {file} aktualisiert.")
                except Exception:
                    log.exception(f"Logfile {file} konnte nicht konvertiert werden.")
        Pub().pub("openWB/system/datastore_version", 16)

    def upgrade_datastore_16(self) -> None:
        for topic, payload in self.all_received_topics.items():
            if re.search("openWB/system/device/[0-9]+/config", topic) is not None:
                payload = decode_payload(payload)
                if payload["type"] == "powerdog":
                    index = get_index(topic)
                    for topic, payload in self.all_received_topics.items():
                        if re.search(f"openWB/system/device/{index}/component/[0-9]+/config", topic) is not None:
                            payload = decode_payload(payload)
                            if payload["type"] == "counter" and payload["configuration"].get("position_evu") is None:
                                payload["configuration"].update({"position_evu": False})
                            Pub().pub(topic.replace("openWB/", "openWB/set/"), payload)
        Pub().pub("openWB/system/datastore_version", 17)
