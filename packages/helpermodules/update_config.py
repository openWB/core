from dataclasses import asdict
import datetime
import glob
import json
import logging
from pathlib import Path
import re
import time
from typing import List, Optional
from paho.mqtt.client import Client as MqttClient, MQTTMessage

import dataclass_utils

from control.chargepoint.chargepoint_template import get_chargepoint_template_default
from helpermodules import timecheck
from helpermodules import hardware_configuration
from helpermodules.broker import InternalBrokerClient
from helpermodules.constants import NO_ERROR
from helpermodules.hardware_configuration import (
    get_hardware_configuration_setting,
    update_hardware_configuration,
    get_serial_number
)
from helpermodules.measurement_logging.process_log import get_default_charge_log_columns, get_totals
from helpermodules.measurement_logging.write_log import get_names
from helpermodules.messaging import MessageType, pub_system_message
from helpermodules.pub import Pub
from helpermodules.utils.json_file_handler import write_and_check
from helpermodules.utils.run_command import run_command
from helpermodules.utils.topic_parser import decode_payload, get_index, get_second_index
from control import counter_all
from control.bat_all import BatConsiderationMode
from control.chargepoint.charging_type import ChargingType
from control.counter import get_counter_default_config
from control.ev.charge_template import get_charge_template_default
from control.ev import ev
from control.ev.ev_template import EvTemplateData
from control.general import ChargemodeConfig, Prices
from control.optional_data import Ocpp
from modules.common.abstract_vehicle import GeneralVehicleConfig
from modules.common.component_type import ComponentType
from modules.devices.sungrow.sungrow.version import Version
from modules.display_themes.cards.config import CardsDisplayTheme
from modules.ripple_control_receivers.gpio.config import GpioRcr
from modules.web_themes.standard_legacy.config import StandardLegacyWebTheme
from modules.devices.good_we.good_we.version import GoodWeVersion

log = logging.getLogger(__name__)

NO_MODULE = {"type": None, "configuration": {}}


class UpdateConfig:
    DATASTORE_VERSION = 73
    valid_topic = [
        "^openWB/bat/config/configured$",
        "^openWB/bat/config/power_limit_mode$",
        "^openWB/bat/set/charging_power_left$",
        "^openWB/bat/set/regulate_up$",
        "^openWB/bat/get/fault_state$",
        "^openWB/bat/get/fault_str$",
        "^openWB/bat/get/power_limit_controllable$",
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
        "^openWB/bat/[0-9]+/get/power_limit_controllable$",
        "^openWB/bat/[0-9]+/set/power_limit$",

        "^openWB/chargepoint/get/power$",
        "^openWB/chargepoint/get/exported$",
        "^openWB/chargepoint/get/imported$",
        "^openWB/chargepoint/get/daily_exported$",
        "^openWB/chargepoint/get/daily_imported$",
        "^openWB/chargepoint/template/[0-9]+$",
        "^openWB/chargepoint/template/[0-9]+/autolock/[0-9]+$",
        "^openWB/chargepoint/[0-9]+/config$",
        "^openWB/chargepoint/[0-9]+/control_parameter/submode$",
        "^openWB/chargepoint/[0-9]+/control_parameter/chargemode$",
        "^openWB/chargepoint/[0-9]+/control_parameter/current_plan$",
        "^openWB/chargepoint/[0-9]+/control_parameter/imported_at_plan_start$",
        "^openWB/chargepoint/[0-9]+/control_parameter/imported_instant_charging$",
        "^openWB/chargepoint/[0-9]+/control_parameter/limit$",
        "^openWB/chargepoint/[0-9]+/control_parameter/prio$",
        "^openWB/chargepoint/[0-9]+/control_parameter/required_current$",
        "^openWB/chargepoint/[0-9]+/control_parameter/timestamp_last_phase_switch$",
        "^openWB/chargepoint/[0-9]+/control_parameter/timestamp_switch_on_off$",
        "^openWB/chargepoint/[0-9]+/control_parameter/used_amount_instant_charging$",
        "^openWB/chargepoint/[0-9]+/control_parameter/phases$",
        "^openWB/chargepoint/[0-9]+/control_parameter/state$",
        "^openWB/chargepoint/[0-9]+/get/charge_state$",
        "^openWB/chargepoint/[0-9]+/get/currents$",
        "^openWB/chargepoint/[0-9]+/get/evse_current$",
        "^openWB/chargepoint/[0-9]+/get/fault_state$",
        "^openWB/chargepoint/[0-9]+/get/fault_str$",
        "^openWB/chargepoint/[0-9]+/get/frequency$",
        "^openWB/chargepoint/[0-9]+/get/max_evse_current$",
        "^openWB/chargepoint/[0-9]+/get/plug_state$",
        "^openWB/chargepoint/[0-9]+/get/phases_in_use$",
        "^openWB/chargepoint/[0-9]+/get/exported$",
        "^openWB/chargepoint/[0-9]+/get/imported$",
        "^openWB/chargepoint/[0-9]+/get/daily_exported$",
        "^openWB/chargepoint/[0-9]+/get/daily_imported$",
        "^openWB/chargepoint/[0-9]+/get/power$",
        "^openWB/chargepoint/[0-9]+/get/powers$",
        "^openWB/chargepoint/[0-9]+/get/power_factors$",
        "^openWB/chargepoint/[0-9]+/get/vehicle_id$",
        "^openWB/chargepoint/[0-9]+/get/voltages$",
        "^openWB/chargepoint/[0-9]+/get/serial_number$",
        "^openWB/chargepoint/[0-9]+/get/soc$",
        "^openWB/chargepoint/[0-9]+/get/soc_timestamp$",
        "^openWB/chargepoint/[0-9]+/get/simulation$",
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
        "^openWB/chargepoint/[0-9]+/set/plug_state_prev$",
        "^openWB/chargepoint/[0-9]+/set/plug_time$",
        "^openWB/chargepoint/[0-9]+/set/rfid$",
        "^openWB/chargepoint/[0-9]+/set/log$",
        "^openWB/chargepoint/[0-9]+/set/phases_to_use$",
        "^openWB/chargepoint/[0-9]+/set/charging_ev_prev$",
        "^openWB/chargepoint/[0-9]+/set/ocpp_transaction_id$",
        "^openWB/chargepoint/[0-9]+/set/ocpp_transaction_active$",

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

        "^openWB/counter/config/consider_less_charging$",
        "^openWB/counter/config/home_consumption_source_id$",
        "^openWB/counter/get/hierarchy$",
        "^openWB/counter/set/disengageable_smarthome_power$",
        "^openWB/counter/set/imported_home_consumption$",
        "^openWB/counter/set/invalid_home_consumption$",
        "^openWB/counter/set/home_consumption$",
        "^openWB/counter/set/daily_yield_home_consumption$",
        "^openWB/counter/set/simulation$",
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
        "^openWB/counter/[0-9]+/set/error_timer$",
        "^openWB/counter/[0-9]+/set/released_surplus$",
        "^openWB/counter/[0-9]+/set/reserved_surplus$",
        "^openWB/counter/[0-9]+/config/max_power_errorcase$",
        "^openWB/counter/[0-9]+/config/max_currents$",
        "^openWB/counter/[0-9]+/config/max_total_power$",

        "^openWB/general/extern$",
        "^openWB/general/extern_display_mode$",
        "^openWB/general/charge_log_data_config$",
        "^openWB/general/control_interval$",
        "^openWB/general/external_buttons_hw$",
        "^openWB/general/grid_protection_configured$",
        "^openWB/general/grid_protection_active$",
        "^openWB/general/http_api$",
        "^openWB/general/modbus_control$",
        "^openWB/general/mqtt_bridge$",
        "^openWB/general/grid_protection_timestamp$",
        "^openWB/general/grid_protection_random_stop$",
        "^openWB/general/range_unit$",
        "^openWB/general/notifications/selected$",
        "^openWB/general/notifications/configuration$",
        "^openWB/general/notifications/start_charging$",
        "^openWB/general/notifications/stop_charging$",
        "^openWB/general/notifications/plug$",
        "^openWB/general/notifications/smart_home$",
        "^openWB/general/ripple_control_receiver/configured$",
        "^openWB/general/ripple_control_receiver/module$",
        "^openWB/general/ripple_control_receiver/get/fault_state$",
        "^openWB/general/ripple_control_receiver/get/fault_str$",
        "^openWB/general/ripple_control_receiver/get/override_value$",
        "^openWB/general/ripple_control_receiver/override_reference$",
        "^openWB/general/chargemode_config/unbalanced_load_limit$",
        "^openWB/general/chargemode_config/unbalanced_load$",
        "^openWB/general/chargemode_config/pv_charging/bat_mode$",
        "^openWB/general/chargemode_config/pv_charging/feed_in_yield$",
        "^openWB/general/chargemode_config/pv_charging/switch_on_threshold$",
        "^openWB/general/chargemode_config/pv_charging/switch_on_delay$",
        "^openWB/general/chargemode_config/pv_charging/switch_off_threshold$",
        "^openWB/general/chargemode_config/pv_charging/switch_off_delay$",
        "^openWB/general/chargemode_config/phase_switch_delay$",
        "^openWB/general/chargemode_config/pv_charging/control_range$",
        "^openWB/general/chargemode_config/pv_charging/phases_to_use$",
        "^openWB/general/chargemode_config/pv_charging/min_bat_soc$",
        "^openWB/general/chargemode_config/pv_charging/bat_power_discharge$",
        "^openWB/general/chargemode_config/pv_charging/bat_power_discharge_active$",
        "^openWB/general/chargemode_config/pv_charging/bat_power_reserve$",
        "^openWB/general/chargemode_config/pv_charging/bat_power_reserve_active$",
        "^openWB/general/chargemode_config/retry_failed_phase_switches$",
        "^openWB/general/chargemode_config/scheduled_charging/phases_to_use$",
        "^openWB/general/chargemode_config/scheduled_charging/phases_to_use_pv$",
        "^openWB/general/chargemode_config/instant_charging/phases_to_use$",
        "^openWB/general/chargemode_config/time_charging/phases_to_use$",
        # obsolet, Daten hieraus müssen nach prices/ überführt werden
        "^openWB/general/price_kwh$",
        "^openWB/general/prices/bat$",
        "^openWB/general/prices/grid$",
        "^openWB/general/prices/pv$",
        "^openWB/general/web_theme$",

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

        "^openWB/optional/et/get/fault_state$",
        "^openWB/optional/et/get/fault_str$",
        "^openWB/optional/et/get/prices$",
        "^openWB/optional/et/provider$",
        "^openWB/optional/int_display/active$",
        "^openWB/optional/int_display/detected$",
        "^openWB/optional/int_display/on_if_plugged_in$",
        "^openWB/optional/int_display/pin_active$",
        "^openWB/optional/int_display/pin_code$",
        "^openWB/optional/int_display/standby$",
        "^openWB/optional/int_display/rotation$",
        "^openWB/optional/int_display/theme$",
        "^openWB/optional/int_display/only_local_charge_points",
        "^openWB/optional/led/active$",
        "^openWB/optional/monitoring/config$",
        "^openWB/optional/rfid/active$",
        "^openWB/optional/ocpp/config$",

        "^openWB/pv/config/configured$",
        "^openWB/pv/get/exported$",
        "^openWB/pv/get/fault_state$",
        "^openWB/pv/get/fault_str$",
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

        "^openWB/vehicle/set/vehicle_update_completed$",
        "^openWB/vehicle/template/ev_template/[0-9]+$",
        "^openWB/vehicle/template/charge_template/[0-9]+/time_charging/plans/[0-9]+$",
        "^openWB/vehicle/template/charge_template/[0-9]+/chargemode/scheduled_charging/plans/[0-9]+$",
        "^openWB/vehicle/template/charge_template/[0-9]+",
        "^openWB/vehicle/[0-9]+/charge_template$",
        "^openWB/vehicle/[0-9]+/ev_template$",
        "^openWB/vehicle/[0-9]+/name$",
        "^openWB/vehicle/[0-9]+/info$",
        "^openWB/vehicle/[0-9]+/soc_module/calculated_soc_state$",
        "^openWB/vehicle/[0-9]+/soc_module/config$",
        "^openWB/vehicle/[0-9]+/soc_module/general_config$",
        "^openWB/vehicle/[0-9]+/tag_id$",
        "^openWB/vehicle/[0-9]+/get/fault_state$",
        "^openWB/vehicle/[0-9]+/get/fault_str$",
        "^openWB/vehicle/[0-9]+/get/force_soc_update$",
        "^openWB/vehicle/[0-9]+/get/range$",
        "^openWB/vehicle/[0-9]+/get/soc$",
        "^openWB/vehicle/[0-9]+/get/soc_request_timestamp$",
        "^openWB/vehicle/[0-9]+/get/soc_timestamp$",
        "^openWB/vehicle/[0-9]+/match_ev/selected$",
        "^openWB/vehicle/[0-9]+/match_ev/tag_id$",
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
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_idmueb$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_ip$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_lambdaueb$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_leistungurl$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_manual_control$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_manwatt$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_maxeinschaltdauer$",
        "^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_maxueb$",
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
        "^openWB/LegacySmartHome/Devices/[0-9]+/device_manual_control$",
        "^openWB/LegacySmartHome/Devices/[0-9]+/mode$",
        "^openWB/LegacySmartHome/Devices/[0-9]+/WHImported_temp$",
        "^openWB/LegacySmartHome/Devices/[0-9]+/RunningTimeToday$",
        "^openWB/LegacySmartHome/Devices/[0-9]+/oncountnor$",
        "^openWB/LegacySmartHome/Devices/[0-9]+/OnCntStandby$",
        "^openWB/LegacySmartHome/Devices/[1-2]+/TemperatureSensor[0-2]$",
        "^openWB/LegacySmartHome/Status/maxspeicherladung$",
        "^openWB/LegacySmartHome/Status/wattnichtschalt$",
        "^openWB/LegacySmartHome/Status/wattnichtHaus$",
        "^openWB/LegacySmartHome/Status/uberschuss$",
        "^openWB/LegacySmartHome/Status/uberschussoffset$",

        "^openWB/system/available_branches",
        "^openWB/system/backup_cloud/config$",
        "^openWB/system/boot_done$",
        "^openWB/system/configurable/backup_clouds$",
        "^openWB/system/backup_cloud/backup_before_update$",
        "^openWB/system/configurable/chargepoints$",
        "^openWB/system/configurable/chargepoints_internal$",
        "^openWB/system/configurable/devices_components$",
        "^openWB/system/configurable/electricity_tariffs$",
        "^openWB/system/configurable/display_themes$",
        "^openWB/system/configurable/monitoring$",
        "^openWB/system/configurable/ripple_control_receivers$",
        "^openWB/system/configurable/soc_modules$",
        "^openWB/system/configurable/web_themes$",
        "^openWB/system/current_branch",
        "^openWB/system/current_branch_commit",
        "^openWB/system/current_commit",
        "^openWB/system/current_missing_commits",
        "^openWB/system/dataprotection_acknowledged$",
        "^openWB/system/installAssistantDone$",
        "^openWB/system/datastore_version",
        "^openWB/system/debug_level$",
        "^openWB/system/device/[0-9]+/component/[0-9]+/config$",
        "^openWB/system/device/[0-9]+/component/[0-9]+/simulation$",
        "^openWB/system/device/[0-9]+/component/[0-9]+/simulation/power_present$",
        "^openWB/system/device/[0-9]+/component/[0-9]+/simulation/present_exported$",
        "^openWB/system/device/[0-9]+/component/[0-9]+/simulation/present_imported$",
        "^openWB/system/device/[0-9]+/component/[0-9]+/simulation/timestamp_present$",
        "^openWB/system/device/[0-9]+/config$",
        "^openWB/system/device/module_update_completed$",
        "^openWB/system/ip_address$",
        "^openWB/system/lastlivevaluesJson$",
        "^openWB/system/mqtt/bridge/[0-9]+$",
        "^openWB/system/mqtt/valid_partner_ids$",
        "^openWB/system/release_train$",
        "^openWB/system/time$",
        "^openWB/system/update_in_progress$",
        "^openWB/system/usage_terms_acknowledged$",
        "^openWB/system/version$",
    ]
    default_topic = (
        ("openWB/bat/config/configured", False),
        ("openWB/bat/config/power_limit_mode", "no_limit"),
        ("openWB/bat/get/fault_state", 0),
        ("openWB/bat/get/fault_str", NO_ERROR),
        ("openWB/bat/get/power_limit_controllable", False),
        ("openWB/chargepoint/get/power", 0),
        ("openWB/chargepoint/template/0", get_chargepoint_template_default()),
        ("openWB/counter/get/hierarchy", []),
        ("openWB/counter/config/consider_less_charging", counter_all.Config().consider_less_charging),
        ("openWB/counter/config/home_consumption_source_id", counter_all.Config().home_consumption_source_id),
        ("openWB/vehicle/0/name", "Standard-Fahrzeug"),
        ("openWB/vehicle/0/info", {"manufacturer": None, "model": None}),
        ("openWB/vehicle/0/charge_template", ev.Ev(0).charge_template.ct_num),
        ("openWB/vehicle/0/soc_module/config", NO_MODULE),
        ("openWB/vehicle/0/soc_module/general_config", dataclass_utils.asdict(GeneralVehicleConfig())),
        ("openWB/vehicle/0/ev_template", ev.Ev(0).ev_template.et_num),
        ("openWB/vehicle/0/tag_id", ev.Ev(0).data.tag_id),
        ("openWB/vehicle/0/get/soc", ev.Ev(0).data.get.soc),
        ("openWB/vehicle/template/ev_template/0", asdict(EvTemplateData(name="Standard-Fahrzeug-Profil",
                                                                        min_current=10))),
        ("openWB/vehicle/template/charge_template/0", get_charge_template_default()),
        ("openWB/general/charge_log_data_config", get_default_charge_log_columns()),
        ("openWB/general/chargemode_config/instant_charging/phases_to_use", 3),
        ("openWB/general/chargemode_config/pv_charging/bat_mode", BatConsiderationMode.EV_MODE.value),
        ("openWB/general/chargemode_config/pv_charging/bat_power_discharge", 1000),
        ("openWB/general/chargemode_config/pv_charging/bat_power_discharge_active", True),
        ("openWB/general/chargemode_config/pv_charging/min_bat_soc", 50),
        ("openWB/general/chargemode_config/pv_charging/bat_power_reserve", 200),
        ("openWB/general/chargemode_config/pv_charging/bat_power_reserve_active", True),
        ("openWB/general/chargemode_config/pv_charging/control_range", [0, 230]),
        ("openWB/general/chargemode_config/pv_charging/switch_off_threshold", 50),
        ("openWB/general/chargemode_config/pv_charging/switch_off_delay", 60),
        ("openWB/general/chargemode_config/pv_charging/switch_on_delay", 30),
        ("openWB/general/chargemode_config/pv_charging/switch_on_threshold", 1500),
        ("openWB/general/chargemode_config/pv_charging/feed_in_yield", 0),
        ("openWB/general/chargemode_config/phase_switch_delay", 7),
        ("openWB/general/chargemode_config/pv_charging/phases_to_use", 0),
        ("openWB/general/chargemode_config/retry_failed_phase_switches",
         ChargemodeConfig().retry_failed_phase_switches),
        ("openWB/general/chargemode_config/scheduled_charging/phases_to_use", 0),
        ("openWB/general/chargemode_config/scheduled_charging/phases_to_use_pv", 0),
        ("openWB/general/chargemode_config/time_charging/phases_to_use", 1),
        ("openWB/general/chargemode_config/unbalanced_load", False),
        ("openWB/general/chargemode_config/unbalanced_load_limit", 18),
        ("openWB/general/control_interval", 10),
        ("openWB/general/extern", False),
        ("openWB/general/extern_display_mode", "primary"),
        ("openWB/general/external_buttons_hw", False),
        ("openWB/general/grid_protection_configured", True),
        ("openWB/general/http_api", False),
        ("openWB/general/modbus_control", False),
        ("openWB/general/notifications/selected", "none"),
        ("openWB/general/notifications/plug", False),
        ("openWB/general/notifications/start_charging", False),
        ("openWB/general/notifications/stop_charging", False),
        ("openWB/general/notifications/smart_home", False),
        ("openWB/general/notifications/configuration", {}),
        ("openWB/general/prices/bat", Prices().bat),
        ("openWB/general/prices/grid", Prices().grid),
        ("openWB/general/prices/pv", Prices().pv),
        ("openWB/general/range_unit", "km"),
        ("openWB/general/ripple_control_receiver/module", NO_MODULE),
        ("openWB/general/web_theme", dataclass_utils.asdict(StandardLegacyWebTheme())),
        ("openWB/graph/config/duration", 120),
        ("openWB/internal_chargepoint/0/data/parent_cp", None),
        ("openWB/internal_chargepoint/1/data/parent_cp", None),
        ("openWB/optional/et/provider", NO_MODULE),
        ("openWB/optional/int_display/active", True),
        ("openWB/optional/int_display/detected", True),
        ("openWB/optional/int_display/on_if_plugged_in", True),
        ("openWB/optional/int_display/pin_active", False),
        ("openWB/optional/int_display/pin_code", "0000"),
        ("openWB/optional/int_display/standby", 60),
        ("openWB/optional/int_display/rotation", 0),
        ("openWB/optional/int_display/theme", dataclass_utils.asdict(CardsDisplayTheme())),
        ("openWB/optional/int_display/only_local_charge_points", False),
        ("openWB/optional/led/active", False),
        ("openWB/optional/monitoring/config", NO_MODULE),
        ("openWB/optional/ocpp/config", dataclass_utils.asdict(Ocpp())),
        ("openWB/optional/rfid/active", False),
        ("openWB/system/backup_cloud/config", NO_MODULE),
        ("openWB/system/backup_cloud/backup_before_update", True),
        ("openWB/system/installAssistantDone", False),
        ("openWB/system/dataprotection_acknowledged", False),
        ("openWB/system/datastore_version", DATASTORE_VERSION),
        ("openWB/system/usage_terms_acknowledged", False),
        ("openWB/system/debug_level", 30),
        ("openWB/system/device/module_update_completed", True),
        ("openWB/system/ip_address", "unknown"),
        ("openWB/system/mqtt/valid_partner_ids", []),
        ("openWB/system/release_train", "master"),
        ("openWB/system/serial_number", get_serial_number()),
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
        self.base_path = Path(__file__).resolve().parents[2]

    def update(self):
        log.debug("Broker-Konfiguration aktualisieren")
        InternalBrokerClient("update-config", self.on_connect, self.on_message).start_finite_loop()
        try:
            # erst breaking changes auflösen, sonst sind alte Topics schon gelöscht
            self.__solve_breaking_changes()
            self.__remove_outdated_topics()
            self._remove_invalid_topics()
            self.__pub_missing_defaults()
            self.__update_version()
        except Exception:
            log.exception("Fehler bei der Aktualisierung des Brokers.")
            pub_system_message({}, "Fehler bei der Aktualisierung der Konfiguration des Brokers.", MessageType.ERROR)
        finally:
            self.__update_topic("openWB/system/update_config_completed", True)

    def on_connect(self, client: MqttClient, userdata, flags: dict, rc: int):
        """ connect to broker and subscribe to set topics
        """
        client.subscribe("openWB/#", 2)

    def on_message(self, client: MqttClient, userdata, msg: MQTTMessage):
        self.all_received_topics.update({msg.topic: msg.payload})

    def __update_topic(self, topic: str, payload):
        """ publish topic to broker and update all_received_topics
        set- and sub-data are not yet initialized, so we have to publish directly into the topic without adding "set/"
        """
        Pub().pub(topic, payload)
        if payload == "":
            del self.all_received_topics[topic]
        else:
            self.all_received_topics[topic] = payload

    def __remove_outdated_topics(self):
        """ remove outdated topics from all_received_topics and broker
        take care with dynamic branches! e.g. vehicle/x/...
        """
        # deleting list items while in iteration throws runtime error, so we collect all topics to delete
        removed_topics = []
        for topic in self.all_received_topics.keys():
            for valid_topic in self.valid_topic:
                if re.search(valid_topic, topic) is not None:
                    break
            else:
                log.debug(f"Ungültiges Topic zum Startzeitpunkt: {topic}")
                removed_topics += [topic]
        # delete topics to allow setting new defaults afterwards
        for topic in removed_topics:
            self.__update_topic(topic, "")

    def _remove_invalid_topics(self):
        """ remove invalid topics from all_received_topics and broker
        """
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
            self.__update_topic(topic, "")

    def __pub_missing_defaults(self):
        """ publish missing required default topics to broker and update all_received_topics
        """
        missing_topics = {}
        for topic, default_payload in self.default_topic:
            if topic not in self.all_received_topics.keys():
                log.debug(f"Setze Topic '{topic}' auf Standardwert '{str(default_payload)}'")
                missing_topics[topic] = default_payload
        for topic, payload in missing_topics.items():
            self.__update_topic(topic, payload)

    def __update_version(self):
        """ update openWB/system/version topic with current version from filesystem
        """
        with open(self.base_path / "web" / "version", "r") as f:
            version = f.read().splitlines()[0]
        self.__update_topic("openWB/system/version", version)

    def __solve_breaking_changes(self) -> None:
        """ solve breaking changes in the datastore
        """
        datastore_version = (decode_payload(self.all_received_topics.get("openWB/system/datastore_version")) or
                             self.DATASTORE_VERSION)
        log.debug(f"current datastore version: {datastore_version}")
        log.debug(f"target datastore version: {self.DATASTORE_VERSION}")
        for version in range(datastore_version, self.DATASTORE_VERSION):
            try:
                log.debug(f"upgrading datastore from version '{version}' to '{version + 1}'")
                getattr(self, f"upgrade_datastore_{version}")()
            except AttributeError:
                log.error(f"missing upgrade function! '{version}'")

    def _loop_all_received_topics(self, callback) -> None:
        modified_topics = {}
        for topic, payload in self.all_received_topics.items():
            try:
                updated_topics = callback(topic, payload)
                if updated_topics is not None:
                    modified_topics.update(updated_topics)
            except Exception:
                log.exception(f"Fehler beim Aktualisieren von '{topic}' mit Payload '{payload}'")
        for topic, payload in modified_topics.items():
            self.__update_topic(topic, payload)

    def upgrade_datastore_0(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            modified_topics = {}
            # prevent_switch_stop auf zwei Einstellungen prevent_phase_switch und prevent_charge_stop aufteilen
            if "openWB/vehicle/template/ev_template/" in topic:
                payload = decode_payload(payload)
                if "prevent_switch_stop" in payload:
                    combined_setting = payload["prevent_switch_stop"]
                    payload.pop("prevent_switch_stop")
                    payload.update({"prevent_charge_stop": combined_setting, "prevent_phase_switch": combined_setting})
                    modified_topics[topic] = payload
            # Alpha2
            # zu konfiguriertem Wechselrichter die maximale Ausgangsleistung hinzufügen
            regex = re.search("(openWB/pv/[0-9]+)/get/fault_state", topic)
            if regex is not None:
                module = regex.group(1)
                if f"{module}/config/max_ac_out" not in self.all_received_topics.keys():
                    modified_topics[f"{module}/config/max_ac_out"] = 0

            # prevent_switch_stop auf zwei Einstellungen prevent_phase_switch und prevent_charge_stop aufteilen
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
                                modified_topics[topic] = updated_payload
                elif payload["type"] == "json":
                    index = get_index(topic)
                    for topic, payload in self.all_received_topics.items():
                        if re.search(f"^openWB/system/device/{index}/component/[0-9]+/config$", topic) is not None:
                            payload = decode_payload(payload)
                            if payload["type"] == "inverter" and "jq_counter" in payload["configuration"]:
                                updated_payload = payload
                                updated_payload["configuration"]["jq_exported"] = payload["configuration"]["jq_counter"]
                                updated_payload["configuration"].pop("jq_counter")
                                modified_topics[topic] = updated_payload
                elif payload["type"] == "byd":
                    updated_payload = payload
                    updated_payload["configuration"]["user"] = payload["configuration"]["username"]
                    updated_payload["configuration"].pop("username")
                    modified_topics[topic] = updated_payload
                elif payload["type"] == "good_we":
                    updated_payload = payload
                    updated_payload["configuration"]["modbus_id"] = payload["configuration"]["id"]
                    updated_payload["configuration"].pop("id")
                    modified_topics[topic] = updated_payload
            return modified_topics

        def upgrade_logs() -> None:
            # Alpha 3
            # Summen in Tages- und Monats-Log hinzufügen
            files = glob.glob(str(self.base_path / "data" / "daily_log") + "/*")
            files.extend(glob.glob(str(self.base_path / "data" / "monthly_log") + "/*"))
            files.sort()
            for file in files:
                with open(file, "r+") as jsonFile:
                    try:
                        content = json.load(jsonFile)
                        if isinstance(content, List):
                            try:
                                new_content = {"entries": content, "totals": get_totals(content)}
                                jsonFile.seek(0)
                                json.dump(new_content, jsonFile)
                                jsonFile.truncate()
                                log.debug(f"Format der Logdatei '{file}' aktualisiert.")
                            except Exception:
                                log.exception(f"Logfile '{file}' entspricht nicht dem Dateiformat von Alpha 3.")
                    except json.decoder.JSONDecodeError:
                        log.exception(f"Logfile '{file}' konnte nicht konvertiert werden, "
                                      "da es keine gültigen json-Daten enthält.")
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
                        log.exception(f"Logfile '{file}' konnte nicht konvertiert werden.")

        self._loop_all_received_topics(upgrade)
        upgrade_logs()
        self.__update_topic("openWB/system/datastore_version", 1)

    def upgrade_datastore_1(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            def convert_ws_to_wh(value: float) -> float:
                return value / 3600

            def get_decoded_value(name: str) -> float:
                return decode_payload(self.all_received_topics[f"{simulation_topic}/{name}"])

            if re.search("^openWB/system/device/[0-9]+/component/[0-9]+/config$", topic) is not None:
                simulation_topic = (f"openWB/system/device/{get_index(topic)}/component/"
                                    f"{get_second_index(topic)}/simulation")
                if self.all_received_topics.get(f"{simulation_topic}/timestamp_present"):
                    modified_topics = {}
                    modified_topics[simulation_topic] = {
                        "timestamp": float(get_decoded_value("timestamp_present")),
                        "power": get_decoded_value("power_present"),
                        "imported": convert_ws_to_wh(get_decoded_value("present_imported")),
                        "exported": convert_ws_to_wh(get_decoded_value("present_exported"))
                    }
                    modified_topics[f"{simulation_topic}/timestamp_present"] = ""
                    modified_topics[f"{simulation_topic}/power_present"] = ""
                    modified_topics[f"{simulation_topic}/present_imported"] = ""
                    modified_topics[f"{simulation_topic}/present_exported"] = ""
                    return modified_topics
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 2)

    def upgrade_datastore_2(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search(
                    "openWB/vehicle/template/charge_template/[0-9]+/chargemode/scheduled_charging/plans/[0-9]+",
                    topic) is not None:
                payload = decode_payload(payload)
                if payload["limit"].get("soc"):
                    updated_payload = payload
                    updated_payload["limit"]["soc_scheduled"] = payload["limit"]["soc"]
                    updated_payload["limit"]["soc_limit"] = payload["limit"]["soc"]
                    updated_payload["limit"].pop("soc")
                    return {topic: updated_payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 3)

    def upgrade_datastore_3(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search(
                    "openWB/vehicle/template/charge_template/[0-9]+/time_charging/plans/[0-9]+",
                    topic) is not None:
                payload = decode_payload(payload)
                if "limit" not in payload:
                    updated_payload = payload
                    updated_payload["limit"] = {"selected": "soc", "amount": 1000, "soc": 70}
                    return {topic: updated_payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 4)

    def upgrade_datastore_4(self) -> None:
        moved_file = False
        for path in Path("/etc/mosquitto/conf.d").glob('99-bridge-openwb-*.conf'):
            run_command(["sudo", "mv", str(path), str(path).replace("conf.d", "conf_local.d")], process_exception=True)
            moved_file = True
        self.__update_topic("openWB/system/datastore_version", 5)
        if moved_file:
            time.sleep(1)
            run_command([str(self.base_path / "runs" / "reboot.sh")], process_exception=True)

    def upgrade_datastore_5(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/chargepoint/template/[0-9]+", topic) is not None:
                payload = decode_payload(payload)
                if "max_current_single_phase" not in payload:
                    updated_payload = payload
                    updated_payload["max_current_single_phase"] = 32
                    updated_payload["max_current_multi_phases"] = 32
                    return {topic: updated_payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 6)

    def upgrade_datastore_6(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/chargepoint/template/[0-9]+$", topic) is not None:
                payload = decode_payload(payload)
                if "plans" in payload["autolock"]:
                    payload["autolock"].pop("plans")
                    return {topic: payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 7)

    def upgrade_datastore_7(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/vehicle/template/ev_template/[0-9]+$", topic) is not None:
                payload = decode_payload(payload)
                if "keep_charge_active_duration" not in payload:
                    payload["keep_charge_active_duration"] = ev.EvTemplateData().keep_charge_active_duration
                    return {topic: payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 8)

    def upgrade_datastore_8(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
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
                    return {topic: payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 9)

    def upgrade_datastore_9(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("^openWB/system/mqtt/bridge/[0-9]+$", topic) is not None:
                payload = decode_payload(payload)
                if payload["name"] == "openWBCloud" and "access" not in payload:
                    payload["access"] = {"partner": False}
                    log.debug("cloud bridge configuration upgraded")
                    return {topic: payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 10)

    def upgrade_datastore_10(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/vehicle/template/ev_template/[0-9]+$", topic) is not None:
                payload = decode_payload(payload)
                updated_payload = payload
                updated_payload["battery_capacity"] = payload["battery_capacity"] * 1000
                updated_payload["average_consump"] = payload["average_consump"] * 1000
                return {topic: updated_payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 11)

    def upgrade_datastore_11(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/chargepoint/[0-9]+/config$", topic) is not None:
                payload = decode_payload(payload)
                if payload["type"] == "openwb_series2_satellit":
                    if "duo_num" not in payload["configuration"]:
                        payload["configuration"].update({"duo_num": 0})
                        return {topic: payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 12)

    def upgrade_datastore_12(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/vehicle/[0-9]+/soc_module/config", topic) is not None:
                payload = decode_payload(payload)
                index = get_index(topic)
                return {f"openWB/set/vehicle/{index}/soc_module/interval_config":
                        dataclass_utils.asdict(GeneralVehicleConfig())}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 13)

    def upgrade_datastore_13(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/chargepoint/[0-9]+/config$", topic) is not None:
                updated_payload = decode_payload(payload)
                payload = decode_payload(payload)
                if payload["type"] == "internal_openwb" or payload["type"] == "external_openwb":
                    updated_payload["configuration"]["duo_num"] = payload["configuration"]["duo_num"] - 1
                    return {topic: updated_payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 14)

    def upgrade_datastore_14(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/system/device/[0-9]+/config", topic) is not None:
                payload = decode_payload(payload)
                if payload["type"] == "solar_watt":
                    payload["configuration"]["ip_address"] = payload["configuration"]["ip_adress"]
                    payload["configuration"].pop("ip_adress")
                    return {topic: payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 15)

    def upgrade_datastore_15(self) -> None:
        files = glob.glob(str(self.base_path / "data" / "daily_log") + "/*")
        files.extend(glob.glob(str(self.base_path / "data" / "monthly_log") + "/*"))
        files.sort()
        for file in files:
            with open(file, "r+") as jsonFile:
                try:
                    modified = False
                    content = json.load(jsonFile)
                    for entry in content["entries"]:
                        if "sh" not in entry:
                            entry.update({"sh": {}})
                            modified = True
                    if "totals" not in content:
                        content["totals"] = {}
                        modified = True
                    if "sh" not in content["totals"]:
                        content["totals"].update({"sh": {}})
                        modified = True
                    if "names" not in content:
                        content["names"] = get_names(content["totals"], {})
                        modified = True
                    if modified:
                        jsonFile.seek(0)
                        json.dump(content, jsonFile)
                        jsonFile.truncate()
                        log.debug(f"Format der Logdatei '{file}' aktualisiert.")
                except Exception:
                    log.exception(f"Logdatei '{file}' konnte nicht konvertiert werden.")
        self.__update_topic("openWB/system/datastore_version", 16)

    def upgrade_datastore_16(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/system/device/[0-9]+/config", topic) is not None:
                payload = decode_payload(payload)
                if payload["type"] == "powerdog":
                    index = get_index(topic)
                    modified_topics = {}
                    for topic_component, payload_component in self.all_received_topics.items():
                        if re.search(f"openWB/system/device/{index}/component/[0-9]+/config",
                                     topic_component) is not None:
                            payload_component = decode_payload(payload_component)
                            if (
                                payload_component["type"] == "counter" and
                                payload_component["configuration"].get("position_evu") is None
                            ):
                                payload_component["configuration"].update({"position_evu": False})
                                modified_topics[topic_component] = payload_component
                    return modified_topics
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 17)

    def upgrade_datastore_17(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/system/device/[0-9]+/config", topic) is not None:
                payload_device = decode_payload(payload)
                index = get_index(topic)
                if payload_device["type"] == "solarmax":
                    modified_topics = {}
                    for topic_component, payload_component in self.all_received_topics.items():
                        if re.search(f"^openWB/system/device/{index}/component/[0-9]+/config$",
                                     topic_component) is not None:
                            payload_inverter = decode_payload(payload_component)
                            if payload_inverter["type"] == "inverter":
                                payload_inverter["configuration"]["modbus_id"] = payload_device["configuration"][
                                    "modbus_id"]
                                payload_device["configuration"].pop("modbus_id")
                            modified_topics[topic] = payload_device
                            modified_topics[topic_component] = payload_inverter
                    return modified_topics
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 18)

    def upgrade_datastore_18(self) -> None:
        def convert_file(file):
            try:
                with open(file, "r+") as jsonFile:
                    modified = False
                    content = json.load(jsonFile)
                    for entry in content["entries"]:
                        if "hc" not in entry:
                            entry.update({"hc": {}})
                            modified = True
                    if modified:
                        jsonFile.seek(0)
                        json.dump(content, jsonFile)
                        jsonFile.truncate()
                        log.debug(f"Format der Logdatei '{file}' aktualisiert.")
            except FileNotFoundError:
                pass
            except Exception:
                log.exception(f"Logdatei '{file}' konnte nicht konvertiert werden.")
        convert_file(f"{str(self.base_path / 'data' / 'daily_log')}/{timecheck.create_timestamp_YYYYMMDD()}.json")
        convert_file(f"{str(self.base_path / 'data' / 'monthly_log')}/{timecheck.create_timestamp_YYYYMM()}.json")
        self.__update_topic("openWB/system/datastore_version", 19)

    def upgrade_datastore_19(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/internal_chargepoint/[0-1]/data/parent_cp", topic) is not None:
                payload = decode_payload(payload)
                for topic_cp, payload_cp in self.all_received_topics.items():
                    payload_cp = decode_payload(payload_cp)
                    if f"openWB/chargepoint/{payload}/config" == topic_cp:
                        if payload_cp["type"] == "internal_openwb":
                            if int(get_index(topic)) == payload_cp["configuration"]["duo_num"]:
                                break
                else:
                    return {topic: None}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 20)

    def upgrade_datastore_20(self) -> None:
        max_c_socket = get_hardware_configuration_setting("max_c_socket")
        if isinstance(max_c_socket, str):
            update_hardware_configuration({"max_c_socket": int(max_c_socket)})
        elif max_c_socket is None:
            update_hardware_configuration({"max_c_socket": 32})
        self.__update_topic("openWB/system/datastore_version", 21)

    def upgrade_datastore_21(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/vehicle/[0-9]+/soc_module/config", topic) is not None:
                config_payload = decode_payload(payload)
                index = get_index(topic)
                for interval_topic, interval_payload in self.all_received_topics.items():
                    if f"openWB/vehicle/{index}/soc_module/interval_config" == interval_topic:
                        interval_config_payload = decode_payload(interval_payload)
                        general_config = GeneralVehicleConfig(
                            request_interval_charging=interval_config_payload["request_interval_charging"],
                            request_interval_not_charging=interval_config_payload["request_interval_not_charging"],
                            request_only_plugged=interval_config_payload["request_only_plugged"])
                        break
                else:
                    general_config = GeneralVehicleConfig()
                if config_payload["type"] == "manual" and config_payload["configuration"].get("efficiency"):
                    general_config.efficiency = config_payload["configuration"]["efficiency"]*100
                    config_payload["configuration"] = {}
                return {
                    topic.replace("config", "general_config"): asdict(general_config),
                    topic: config_payload
                }
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 22)

    def upgrade_datastore_22(self) -> None:
        files = glob.glob(str(self.base_path / "data" / "charge_log") + "/*")
        files.sort()
        for file in files:
            modified = False
            with open(file, "r+") as jsonFile:
                try:
                    content = json.load(jsonFile)
                    for entry in content:
                        if entry["time"]["time_charged"].endswith(":60"):
                            entry["time"]["time_charged"] = "1:00"
                            modified = True
                    if modified:
                        jsonFile.seek(0)
                        json.dump(content, jsonFile)
                        jsonFile.truncate()
                        log.debug(f"Format des Ladeprotokolls '{file}' aktualisiert.")
                except Exception:
                    log.exception(f"Ladeprotokoll '{file}' konnte nicht aktualisiert werden.")
        self.__update_topic("openWB/system/datastore_version", 23)

    def upgrade_datastore_23(self) -> None:
        def upgrade(topic: str, payload) -> None:
            if re.search("openWB/system/mqtt/bridge/[0-9]+", topic) is not None:
                bridge_configuration = decode_payload(payload)
                if bridge_configuration["remote"]["is_openwb_cloud"]:
                    index = get_index(topic)
                    result = run_command(["php", "-f", str(self.base_path / "runs" / "save_mqtt.php"), index, payload],
                                         process_exception=True)
                    log.info("successfully updated configuration of bridge "
                             f"'{bridge_configuration['name']}' ({index})")
                    pub_system_message(payload, result, MessageType.SUCCESS)
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 24)

    def upgrade_datastore_24(self) -> None:
        # Wenn mehrere EV eine Fahrzeug-Vorlage nutzen, wird die Effizienz des letzten für alle in der Vorlage gesetzt.
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/vehicle/[0-9]+/soc_module/general_config", topic) is not None:
                payload = decode_payload(payload)
                index = get_index(topic)
                modified_topics = {}
                for ev_template_id_topic, ev_template_id_payload in self.all_received_topics.items():
                    if f"openWB/vehicle/{index}/ev_template" == ev_template_id_topic:
                        ev_template_id = decode_payload(ev_template_id_payload)
                        break
                for ev_template_topic, ev_template_payload in self.all_received_topics.items():
                    if f"openWB/vehicle/template/ev_template/{ev_template_id}" == ev_template_topic:
                        ev_template = decode_payload(ev_template_payload)
                        break
                if "efficiency" in payload:
                    ev_template.update({"efficiency": payload["efficiency"]})
                    payload.pop("efficiency")
                    modified_topics[topic] = payload
                modified_topics[ev_template_topic] = ev_template
                return modified_topics
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 25)

    def upgrade_datastore_25(self) -> None:
        files = glob.glob(str(self.base_path / "data" / "charge_log") + "/*")
        files.sort()
        for file in files:
            with open(file, "r+") as jsonFile:
                try:
                    content = json.load(jsonFile)
                    for entry in content:
                        entry["time"]["time_charged"] = timecheck.convert_timedelta_to_time_string(
                            datetime.timedelta(seconds=timecheck.get_difference(
                                entry["time"]["begin"], entry["time"]["end"])))
                    jsonFile.seek(0)
                    json.dump(content, jsonFile)
                    jsonFile.truncate()
                    log.debug(f"Format des Ladeprotokolls '{file}' aktualisiert.")
                except Exception:
                    log.exception(f"Ladeprotokoll '{file}' konnte nicht aktualisiert werden.")
        self.__update_topic("openWB/system/datastore_version", 26)

    def upgrade_datastore_26(self) -> None:
        # module kostal_pico_old: rename "ip_address" in configuration to "url" as we need a complete url
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/system/device/[0-9]+/component/[0-9]+/config", topic) is not None:
                configuration_payload = decode_payload(payload)
                if configuration_payload.get("type") == "kostal_piko_old":
                    configuration_payload["configuration"].update(
                        {"url": configuration_payload["configuration"]["ip_address"]})
                    configuration_payload["configuration"].pop("ip_address")
                    # add protocol "http://" if not already specified
                    if not re.search("^https?://", configuration_payload["configuration"]["url"], re.IGNORECASE):
                        configuration_payload["configuration"]["url"] = (
                            f"http://{configuration_payload['configuration']['url']}")
                    return {topic: configuration_payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 27)

    def upgrade_datastore_27(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            # add "official" flag if display theme "card" is selected
            if re.search("openWB/optional/int_display/theme", topic) is not None:
                configuration_payload = decode_payload(payload)
                if configuration_payload.get("type") == "cards":
                    configuration_payload.update({"official": True})
                    return {topic: configuration_payload}
            # add "official" flag if web theme "standard_legacy" is selected
            if re.search("openWB/general/web_theme", topic) is not None:
                configuration_payload = decode_payload(payload)
                if configuration_payload.get("type") == "standard_legacy":
                    configuration_payload.update({"official": True})
                    return {topic: configuration_payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 28)

    def upgrade_datastore_28(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/vehicle/[0-9]+/soc_module/calculated_soc_state", topic) is not None:
                payload = decode_payload(payload)
                if payload.get("request_start_soc"):
                    payload.pop("request_start_soc")
                    return {topic: payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 29)

    def upgrade_datastore_29(self) -> None:
        """ moved to upgrade_datastore_32
        """
        self.__update_topic("openWB/system/datastore_version", 30)

    def upgrade_datastore_30(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/vehicle/[0-9]+/soc_module/general_config", topic) is not None:
                payload = decode_payload(payload)
                # Zeitangabe in s
                payload["request_interval_charging"] = payload["request_interval_charging"]*60
                payload["request_interval_not_charging"] = payload["request_interval_not_charging"]*60
                return {topic: payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 31)

    def upgrade_datastore_31(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/vehicle/[0-9]+/get/soc_timestamp", topic) is not None:
                payload = decode_payload(payload)
                if payload:
                    updated_payload = datetime.datetime.strptime(payload, "%m/%d/%Y, %H:%M:%S").timestamp()
                    return {topic: updated_payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 32)

    def upgrade_datastore_32(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/vehicle/template/charge_template/[0-9]+$", topic) is not None:
                payload = decode_payload(payload)
                if payload.get("et") is None:
                    updated_payload = payload
                    updated_payload.update({"et": asdict(ev.Et())})
                    return {topic: updated_payload}
            if re.search("^openWB/general/price_kwh$", topic) is not None:
                price = decode_payload(payload)/1000  # €/kWh -> €/Wh
                return {
                    "openWB/set/general/prices/bat": price,
                    "openWB/set/general/prices/grid": price,
                    "openWB/set/general/prices/pv": price
                }
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 33)

    def upgrade_datastore_33(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            # convert price from €/kWh to €/Wh
            if (re.search("openWB/general/prices/bat$", topic) is not None or
                re.search("openWB/general/prices/grid$", topic) is not None or
                    re.search("openWB/general/prices/pv$", topic) is not None):
                payload = decode_payload(payload)
                if payload > 0.01:  # entspricht 10€/kWh
                    updated_payload = payload/1000  # €/kWh -> €/Wh
                    return {topic: updated_payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 34)

    def upgrade_datastore_34(self) -> None:
        def convert_file(file):
            try:
                with open(file, "r+") as jsonFile:
                    modified = False
                    content = json.load(jsonFile)
                    for e in content["entries"]:
                        if type(e["date"]) is not str:
                            old_date = datetime.datetime.fromtimestamp(e["date"])
                            # old version had a bug formatting "date" '$M' <-> '%M'
                            # e["date"] = old_date.strftime('%H:$M')
                            e["date"] = old_date.strftime('%H:%M')
                            modified = True
                        if type(e["timestamp"]) is float:
                            e["timestamp"] = int(e["timestamp"])
                            modified = True
                    if modified:
                        jsonFile.seek(0)
                        json.dump(content, jsonFile)
                        jsonFile.truncate()
                        log.debug(f"Format der Logdatei '{file}' aktualisiert.")
            except FileNotFoundError:
                pass
            except Exception:
                log.exception(f"Logfile '{file}' konnte nicht konvertiert werden.")

        files = glob.glob(str(self.base_path / "data" / "daily_log") + "/*")
        files.sort()
        for file in files:
            convert_file(file)
        # next upgrade only fixes a bug introduced in an earlier version of this method
        # so we can skip upgrade_datastore_35() if this fixed version has run
        self.__update_topic("openWB/system/datastore_version", 36)

    def upgrade_datastore_35(self) -> None:
        def convert_file(file):
            try:
                with open(file, "r+") as jsonFile:
                    modified = False
                    content = json.load(jsonFile)
                    for e in content["entries"]:
                        if type(e["date"]) is str and '$M' in e["date"]:
                            old_timestamp = datetime.datetime.fromtimestamp(e["timestamp"])
                            e["date"] = old_timestamp.strftime('%H:%M')
                            modified = True
                    if modified:
                        jsonFile.seek(0)
                        json.dump(content, jsonFile)
                        jsonFile.truncate()
                        log.debug(f"Format der Logdatei '{file}' aktualisiert.")
            except FileNotFoundError:
                pass
            except Exception:
                log.exception(f"Logfile '{file}' konnte nicht konvertiert werden.")
        files = glob.glob(str(self.base_path / "data" / "daily_log") + "/*")
        files.sort()
        for file in files:
            convert_file(file)
        self.__update_topic("openWB/system/datastore_version", 36)

    def upgrade_datastore_36(self) -> None:
        if hardware_configuration.get_hardware_configuration_setting("ripple_control_receiver_configured", False):
            Pub().pub("openWB/set/general/ripple_control_receiver/module", dataclass_utils.asdict(GpioRcr()))
        hardware_configuration.remove_setting_hardware_configuration("ripple_control_receiver_configured")
        self.__update_topic("openWB/system/datastore_version", 37)

    def upgrade_datastore_37(self) -> None:
        def collect_names(topic: str, payload) -> None:
            if re.search("^openWB/vehicle/[0-9]+/name$", topic) is not None:
                payload = decode_payload(payload)
                names[f"ev{get_index(topic)}"] = payload
            elif re.search("^openWB/chargepoint/[0-9]+/config$", topic) is not None:
                payload = decode_payload(payload)
                names[f"cp{get_index(topic)}"] = payload["name"]
            elif re.search("^openWB/system/device/[0-9]+/component/[0-9]+/config$", topic) is not None:
                payload = decode_payload(payload)
                if "inverter" in payload["type"]:
                    prefix = "pv"
                elif "counter" in payload["type"]:
                    prefix = "counter"
                else:
                    prefix = payload["type"]
                names[f"{prefix}{get_second_index(topic)}"] = payload["name"]
            elif re.search("^openWB/LegacySmartHome/config/get/Devices/[0-9]+/device_name$", topic) is not None:
                names[f"sh{get_index(topic)}"] = decode_payload(payload)

        def convert_file(file):
            log.debug(f"Prüfe Logdatei '{file}'")
            try:
                with open(file, "r+") as jsonFile:
                    content: dict = json.load(jsonFile)
                    new_names = get_names(content["entries"][-1], {}, names)
                    if new_names != content["names"]:
                        content["names"] = new_names
                        jsonFile.seek(0)
                        json.dump(content, jsonFile)
                        jsonFile.truncate()
                        log.debug(f"Format der Logdatei '{file}' aktualisiert.")
            except FileNotFoundError:
                pass
            except Exception:
                log.exception(f"Logfile '{file}' konnte nicht konvertiert werden.")
        names = {}
        self._loop_all_received_topics(collect_names)
        files = glob.glob(str(self.base_path / "data" / "daily_log") + "/*")
        files.extend(glob.glob(str(self.base_path / "data" / "monthly_log") + "/*"))
        files.sort()
        for file in files:
            convert_file(file)
        self.__update_topic("openWB/system/datastore_version", 38)

    def upgrade_datastore_38(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/chargepoint/[0-9]+/set/log$", topic) is not None:
                payload = decode_payload(payload)
                if isinstance(payload["timestamp_start_charging"], str):
                    converted_timestamp = datetime.datetime.strptime(
                        payload["timestamp_start_charging"], "%m/%d/%Y, %H:%M:%S").timestamp()
                    updated_payload = payload
                    updated_payload.update({"timestamp_start_charging": converted_timestamp})
                    return {topic: updated_payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 39)

    def upgrade_datastore_39(self) -> None:
        def upgrade(topic: str, payload) -> None:
            if re.search("openWB/system/device/[0-9]+/config", topic) is not None:
                payload = decode_payload(payload)
                if payload.get("type") == "alpha_ess" and "port" not in payload["configuration"]:
                    if payload["configuration"]["source"] == 1:
                        payload["configuration"].update({"port": 502})
                if payload.get("type") == "kostal_plenticore" and "port" not in payload["configuration"]:
                    payload["configuration"].update({"port": 1502})
                if payload.get("type") == "saxpower" and "port" not in payload["configuration"]:
                    payload["configuration"].update({"port": 3600})
                # modules with port 502
                modified_modules = ["powerdog", "carlo_gavazzi", "e3dc", "good_we",
                                    "huawei", "huawei_smartlogger", "janitza", "kostal_sem", "qcells",
                                    "siemens", "siemens_sentron", "sma_sunny_boy", "sma_sunny_island",
                                    "solarmax", "solax", "studer", "varta", "victron"]
                for i in modified_modules:
                    if payload.get("type") == i and "port" not in payload["configuration"]:
                        payload["configuration"].update({"port": 502})
                Pub().pub(topic, payload)
        self._loop_all_received_topics(upgrade)
        Pub().pub("openWB/system/datastore_version", 40)

    def upgrade_datastore_40(self) -> None:
        def upgrade(topic: str, payload) -> None:
            if re.search("openWB/system/device/[0-9]+", topic) is not None:
                payload = decode_payload(payload)
                # Module mit separater Modbus ID für jede Komponente
                if payload.get("name") == "Sma Sunny Boy/Tripower Speicher"\
                        and "modbus_id" not in payload["configuration"]:
                    payload["configuration"].update({"modbus_id": 3})
                if payload.get("name") == "Sma Sunny Boy Smart Energy Speicher"\
                        and "modbus_id" not in payload["configuration"]:
                    payload["configuration"].update({"modbus_id": 3})
                if payload.get("name") == "Sma Sunny Boy/Tripower Zähler"\
                        and "modbus_id" not in payload["configuration"]:
                    payload["configuration"].update({"modbus_id": 3})
                if payload.get("name") == "Sma Sunny Boy/Tripower Wechselrichter"\
                        and "modbus_id" not in payload["configuration"]:
                    if payload.get("configuration").get("version") == 1:
                        payload["configuration"].update({"modbus_id": 1})
                    elif payload.get("configuration").get("version") == 2:
                        payload["configuration"].update({"modbus_id": 2})
                    else:
                        payload["configuration"].update({"modbus_id": 3})
                if payload.get("name") == "SMA Sunny Island Speicher" and "modbus_id" not in payload["configuration"]:
                    payload["configuration"].update({"modbus_id": 3})

                # Module mit Modbus ID=1 für Gerät (alle Komponenten haben die gleiche ID)
                modified_modules = ["powerdog", "carlo_gavazzi", "e3dc",
                                    "janitza", "siemens", "siemens_sentron", "varta"]
                for i in modified_modules:
                    if payload.get("type") == i and "modbus_id" not in payload["configuration"]:
                        payload["configuration"].update({"modbus_id": 1})

                # Module mit spezieller Modbus ID für Gerät
                if payload.get("type") == "alpha_ess" and "modbus_id" not in payload["configuration"]:
                    payload["configuration"].update({"modbus_id": 85})
                if payload.get("type") == "kostal_plenticore" and "modbus_id" not in payload["configuration"]:
                    payload["configuration"].update({"modbus_id": 71})
                if payload.get("type") == "kostal_sem" and "modbus_id" not in payload["configuration"]:
                    payload["configuration"].update({"modbus_id": 71})
                if payload.get("type") == "saxpower" and "modbus_id" not in payload["configuration"]:
                    payload["configuration"].update({"modbus_id": 64})

                Pub().pub(topic, payload)
        self._loop_all_received_topics(upgrade)
        Pub().pub("openWB/system/datastore_version", 41)

    def upgrade_datastore_41(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if "openWB/general/chargemode_config/pv_charging/bat_prio" == topic:
                old_bat_prio = decode_payload(payload)
                for mode_topic, mode_payload in self.all_received_topics.items():
                    if ("openWB/general/chargemode_config/pv_charging/charging_power_reserve" == mode_topic and
                            decode_payload(mode_payload) == 0 and old_bat_prio is False):
                        return {"openWB/general/chargemode_config/pv_charging/bat_mode": "ev_mode"}
                    elif ("openWB/general/chargemode_config/pv_charging/rundown_power" == mode_topic and
                            decode_payload(mode_payload) == 0 and old_bat_prio):
                        return {"openWB/general/chargemode_config/pv_charging/bat_mode": "bat_mode"}
                else:
                    return {"openWB/general/chargemode_config/pv_charging/bat_mode": "min_soc_bat_mode"}
            elif "openWB/general/chargemode_config/pv_charging/rundown_soc" == topic:
                return {"openWB/general/chargemode_config/pv_charging/min_bat_soc": decode_payload(payload)}
            elif "openWB/general/chargemode_config/pv_charging/rundown_power" == topic:
                return {"openWB/general/chargemode_config/pv_charging/bat_power_discharge": decode_payload(payload)}
            elif "openWB/general/chargemode_config/pv_charging/charging_power_reserve" == topic:
                return {"openWB/general/chargemode_config/pv_charging/bat_power_reserve": decode_payload(payload)}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 42)

    def upgrade_datastore_42(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if "openWB/general/chargemode_config/pv_charging/bat_power_discharge" == topic:
                return {"openWB/general/chargemode_config/pv_charging/bat_power_discharge_active": decode_payload(
                    payload) > 0}
            elif "openWB/general/chargemode_config/pv_charging/bat_power_reserve" == topic:
                return {"openWB/general/chargemode_config/pv_charging/bat_power_reserve_active": decode_payload(
                    payload) > 0}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 43)

    def upgrade_datastore_43(self) -> None:
        def upgrade(topic: str, payload) -> None:
            if re.search("openWB/system/device/[0-9]+", topic) is not None:
                device = decode_payload(payload)
                if device.get("type") == "sungrow" and "version" not in device["configuration"]:
                    device_id = get_index(topic)
                    device_name = device.get("name")
                    version = None
                    inverter_id = None
                    battery_id = None
                    hierarchy = None
                    for other_topic, other_payload in self.all_received_topics.items():
                        if re.search(f"openWB/system/device/{device_id}/component/[0-9]+", other_topic) is not None:
                            component = decode_payload(other_payload)
                            component_id = int(get_second_index(other_topic))
                            if component.get("type") == ComponentType.COUNTER.value \
                               and "version" in component["configuration"]:
                                version = component['configuration']['version']
                                log.debug(f"Version {version} found for device {device_id} '{device_name}'")
                            elif component.get("type") == ComponentType.BAT.value:
                                battery_id = component_id
                            elif component.get("type") == ComponentType.INVERTER.value:
                                inverter_id = component_id
                        elif re.search("openWB/counter/get/hierarchy", other_topic) is not None:
                            hierarchy = decode_payload(other_payload)

                    if battery_id or version == Version.SH:
                        # Assume an SH_WiNet if hybrid inverter, this is compatible to SH_LAN (but not vice versa)
                        version = Version.SH_winet_dongle
                    elif not version:
                        # Assume an SG_WiNet version as default if no battery or version from counter found
                        version = Version.SG_winet_dongle
                    log.debug(f"Setting version {version} for device {device_id} '{device_name}'")
                    device["configuration"].update({"version": version})
                    Pub().pub(topic, device)
                    pub_system_message(device, f"Die Konfiguration von '{device_name}' wurde aktualisiert. "
                                               f"Bitte in den Geräteeinstellungen sicherstellen, dass Version "
                                               f"'{Version(version).name}' korrekt ist", MessageType.INFO)

                    if battery_id and inverter_id and hierarchy:
                        _counter_all = counter_all.CounterAll()
                        _counter_all.data.get.hierarchy = hierarchy
                        _counter_all.hierarchy_remove_item(battery_id)
                        _counter_all.hierarchy_add_item_below(battery_id, ComponentType.BAT, inverter_id)
                        log.debug(f"Moved battery {battery_id} below inverter {inverter_id} in hierarchy")
                        Pub().pub("openWB/counter/get/hierarchy", _counter_all.data.get.hierarchy)

        self._loop_all_received_topics(upgrade)
        Pub().pub("openWB/system/datastore_version", 44)

    def upgrade_datastore_44(self) -> None:
        try:
            corrupt_days = ["20240620", "20240619", "20240618"]
            for topic, payload in self.all_received_topics.items():
                if topic == "openWB/counter/get/hierarchy":
                    top_entry = decode_payload(payload)[0]
                    if top_entry["type"] != "counter":
                        raise Exception("First item in hierarchy must be a counter")
                    evu_counter_str = f"counter{top_entry['id']}"
            for corrupt_day in corrupt_days:
                try:
                    filepath = f"{self.base_path}/data/daily_log/{corrupt_day}.json"
                    with open(filepath, "r") as jsonFile:
                        content = json.load(jsonFile)
                    for entry in content["entries"]:
                        for counter_entry in entry["counter"]:
                            if evu_counter_str == counter_entry and entry["counter"][counter_entry]["grid"] is False:
                                entry["counter"][counter_entry]["grid"] = True
                                break
                        else:
                            log.debug("all grid: False-bug does not exist in this installation")
                            return
                    write_and_check(filepath, content)
                except Exception:
                    log.exception(f"Logdatei '{filepath}' konnte nicht konvertiert werden.")
            try:
                filepath = f"{self.base_path}/data/monthly_log/202406.json"
                with open(filepath, "r") as jsonFile:
                    content = json.load(jsonFile)
                for entry in content["entries"]:
                    if entry["date"] in corrupt_days:
                        for counter_entry in entry["counter"]:
                            if evu_counter_str == counter_entry:
                                entry["counter"][counter_entry]["grid"] = True
                                break
                write_and_check(filepath, content)
            except Exception:
                log.exception(f"Logdatei '{filepath}' konnte nicht konvertiert werden.")
        except Exception:
            log.exception("Fehler beim Konvertieren der Logdateien")
        self.__update_topic("openWB/system/datastore_version", 45)

    def upgrade_datastore_45(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("^openWB/general/chargemode_config/pv_charging/phase_switch_delay$", topic) is not None:
                delay = decode_payload(payload)
                return {
                    "openWB/general/chargemode_config/phase_switch_delay": delay,
                }
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 46)

    def upgrade_datastore_46(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/vehicle/template/charge_template/[0-9]+$", topic) is not None:
                payload = decode_payload(payload)
                if "disable_after_unplug" in payload:
                    updated_payload = payload
                    payload.pop("disable_after_unplug")
                    return {topic: updated_payload}
            if re.search("openWB/chargepoint/template/[0-9]+$", topic) is not None:
                payload = decode_payload(payload)
                if "rfid_enabling" in payload:
                    updated_payload = payload
                    updated_payload["rfid_enabling"] = {}
                    payload.pop("rfid_enabling")
                    return {topic: updated_payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 47)

    def upgrade_datastore_47(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/chargepoint/template/[0-9]+$", topic) is not None:
                payload = decode_payload(payload)
                if "disable_after_unplug" not in payload:
                    updated_payload = payload
                    updated_payload.update({"disable_after_unplug": False})
                    return {topic: updated_payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 48)

    def upgrade_datastore_48(self) -> None:
        def upgrade(topic: str, payload) -> None:
            if re.search("openWB/system/device/[0-9]+", topic) is not None:
                payload = decode_payload(payload)
                # update version and firmware of GoodWe
                if payload.get("type") == "good_we" and "version" not in payload["configuration"]:
                    payload["configuration"].update({"firmware": 8})
                    payload["configuration"].update({"version": GoodWeVersion.V_1_7})
                Pub().pub(topic, payload)
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 49)

    def upgrade_datastore_49(self) -> None:
        Pub().pub("openWB/system/installAssistantDone", True)
        self.all_received_topics.update({"openWB/system/installAssistantDone": "true"})
        Pub().pub("openWB/system/datastore_version", 50)

    def upgrade_datastore_50(self) -> None:
        # es gibt noch Topics von gelöschten Komponenten unter openWB/(counter|pv|bat)/[0-9], aber keine Konfiguration
        # zu den Komponenten.
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/(counter|pv|bat)/[0-9]+", topic) is not None:
                for component_topic in self.all_received_topics.keys():
                    if re.search("openWB/system/device/[0-9]+/component/[0-9]+/config$", component_topic) is not None:
                        if get_second_index(component_topic) == get_index(topic):
                            return
                else:
                    return {topic: ""}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 51)

    def upgrade_datastore_51(self) -> None:
        def upgrade(topic: str, payload) -> None:
            if re.search("openWB/system/device/[0-9]+", topic) is not None:
                payload = decode_payload(payload)
                # remove device type of deye
                if payload.get("type") == "deye" and "device_type" in payload["configuration"]:
                    payload["configuration"].pop("device_type")
                Pub().pub(topic, payload)
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 52)

    def upgrade_datastore_52(self) -> None:
        # PR reverted
        self.__update_topic("openWB/system/datastore_version", 53)

    def upgrade_datastore_53(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if "openWB/optional/int_display/theme" == topic:
                configuration_payload = decode_payload(payload)
                if configuration_payload.get("type") == "cards":
                    if configuration_payload["configuration"].get("enable_energy_flow_view") is None:
                        configuration_payload["configuration"].update({
                            "enable_energy_flow_view": True,
                        })
                    if configuration_payload["configuration"].get("enable_dashboard_card_vehicles") is None:
                        configuration_payload["configuration"].update({
                            "enable_dashboard_card_vehicles": True,
                        })
                    if configuration_payload["configuration"].get("simple_charge_point_view") is None:
                        configuration_payload["configuration"].update({
                            "simple_charge_point_view": True,
                        })
                    return {topic: configuration_payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 54)

    def upgrade_datastore_54(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if "openWB/counter/config/reserve_for_less_charging" == topic:
                payload = decode_payload(payload)
                return {"openWB/counter/config/consider_less_charging": payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 55)

    def upgrade_datastore_55(self) -> None:
        if hardware_configuration.exists_hardware_configuration_setting("dc_charging") is False:
            hardware_configuration.update_hardware_configuration({"dc_charging": False})

        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/chargepoint/template/[0-9]+", topic) is not None:
                payload = decode_payload(payload)
                if "charging_type" not in payload:
                    updated_payload = payload
                    updated_payload["charging_type"] = ChargingType.AC.value
                    return {topic: updated_payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 56)

    def upgrade_datastore_56(self) -> None:
        # es gibt noch Topics von Komponenten gelöschter Geräte
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/system/device/[0-9]+/component/[0-9]+", topic) is not None:
                device_index = get_index(topic)
                for device_topic in self.all_received_topics.keys():
                    if f"openWB/system/device/{device_index}/config" == device_topic:
                        return
                else:
                    log.debug(f"Entferne Topic von gelöschter Komponente {topic}")
                    return {topic: ""}
            elif re.search("openWB/(counter|pv|bat)/[0-9]+", topic) is not None:
                for component_topic in self.all_received_topics.keys():
                    if re.search(f"openWB/system/device/[0-9]+/component/{get_index(topic)}",
                                 component_topic) is not None:
                        device_index = get_index(component_topic)
                        if f"openWB/system/device/{device_index}/config" in self.all_received_topics.keys():
                            return
                else:
                    log.debug(f"Entferne Topic von gelöschter Komponente {topic}")
                    return {topic: ""}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 57)

    def upgrade_datastore_57(self) -> None:
        def upgrade(topic: str, payload) -> None:
            if re.search("openWB/system/device/[0-9]+", topic) is not None:
                payload = decode_payload(payload)
                # add factor for existing SolarEdge externel inverter
                if payload.get("type") == "external_inverter"\
                        and "factor" not in payload["configuration"]:
                    payload["configuration"].update({"factor": 1})
                Pub().pub(topic, payload)
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 58)

    def upgrade_datastore_58(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            # add manufacturer and model to vehicles
            if re.search("openWB/vehicle/[0-9]+/name", topic) is not None:
                vehicle_info_topic = topic.replace("/name", "/info")
                if vehicle_info_topic not in self.all_received_topics:
                    return {vehicle_info_topic: {"manufacturer": None, "model": None}}
            # add manufacturer and model to components
            if re.search("openWB/system/device/[0-9]+/component/[0-9]+/config", topic) is not None:
                config_payload = decode_payload(payload)
                if "info" not in config_payload:
                    config_payload.update({"info": {"manufacturer": None, "model": None}})
                    return {topic: config_payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 59)

    def upgrade_datastore_59(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/system/device/[0-9]+/config", topic) is not None:
                # add "vendor" to devices
                device_config = decode_payload(payload)
                # defaults to vendor = type
                device_vendor = device_config.get("type")
                # 1. generic devices
                if device_config.get("type") in ["http", "json", "mqtt", "virtual"]:
                    device_vendor = "generic"
                # 2. openWB
                if device_config.get("type").startswith("openwb_"):
                    device_vendor = "openwb"
                # 3. huawei
                elif device_config.get("type").startswith("huawei"):
                    device_vendor = "huawei"
                # 4. kostal
                elif device_config.get("type").startswith("kostal"):
                    device_vendor = "kostal"
                # 5. Siemens
                elif device_config.get("type").startswith("siemens"):
                    device_vendor = "siemens"
                # 6 sma
                elif device_config.get("type").startswith("sma_"):
                    device_vendor = "sma"
                elif device_config.get("type") == "sonnenbatterie":
                    device_vendor = "sonnen"
                elif device_config.get("type") == "azzurro_sofar":
                    device_config.update({"type": "sofar"})
                    device_vendor = "sofar"
                # add "vendor" to device
                if "vendor" not in device_config:
                    device_config.update({"vendor": device_vendor})
                    log.debug(f"Added vendor '{device_vendor}' to device '{device_config['name']}'")
                    log.debug(f"Device configuration: {device_config}")
                    return {topic: device_config}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 60)

    def upgrade_datastore_60(self) -> None:
        def upgrade(topic: str, payload) -> None:
            if re.search("openWB/system/device/[0-9]+", topic) is not None:
                payload = decode_payload(payload)
                # remove shelly generation
                if payload.get("type") == "shelly" and "generation" in payload["configuration"]:
                    payload["configuration"].pop("generation")
                # add factor
                if payload.get("type") == "shelly" and "factor" not in payload["configuration"]:
                    payload["configuration"].update({"factor": -1})
                Pub().pub(topic, payload)
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 61)

    def upgrade_datastore_61(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/counter/[0-9]+/config/max_total_power", topic) is not None:
                index = get_index(topic)
                if f"openWB/counter/{index}/config/max_power_errorcase" not in self.all_received_topics.keys():
                    max_power_errorcase = get_counter_default_config()["max_power_errorcase"]
                    return {f"openWB/counter/{index}/config/max_power_errorcase": max_power_errorcase}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 62)

    def upgrade_datastore_62(self) -> None:
        pub_system_message(
            {}, "Bei einem Zählerausfall werden nun 7kW für diesen Zähler freigegeben. Bisher wurde im "
            "Fehlerfall die Ladung gestoppt. Du kannst die maximale Leistung im Fehlerfall für jeden Zähler"
            " unter Einstellungen -> Konfiguration -> Lastmanagement anpassen.", MessageType.WARNING)
        self.__update_topic("openWB/system/datastore_version", 63)

    def upgrade_datastore_63(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if re.search("openWB/bat/[0-9]+/get/power", topic) is not None:
                index = get_index(topic)
                if f"openWB/bat/{index}/get/power_limit_controllable" not in self.all_received_topics.keys():
                    return {f"openWB/bat/{index}/get/power_limit_controllable": False}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 64)

    def upgrade_datastore_64(self) -> None:
        pub_system_message(
            {}, 'Garantieverlängerung für die openWB verfügbar -> '
            '<a href="https://wb-solution.de/shop/">https://wb-solution.de/shop/</a>',
            MessageType.INFO)
        self.__update_topic("openWB/system/datastore_version", 65)

    def upgrade_datastore_65(self) -> None:
        # sungrow version fixed in upgrade_datastore_71
        self.__update_topic("openWB/system/datastore_version", 66)

    def upgrade_datastore_66(self) -> None:
        def upgrade(topic: str, payload) -> None:
            if re.search("openWB/system/device/[0-9]+", topic) is not None:
                payload = decode_payload(payload)
                # add type
                if payload.get("type") == "huawei" and "type" not in payload["configuration"]:
                    payload["configuration"].update({"type": "s_dongle"})
                Pub().pub(topic, payload)
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 67)

    def upgrade_datastore_67(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if "openWB/general/chargemode_config/phase_switch_delay" == topic:
                if decode_payload(payload) < 5:
                    return {"openWB/general/chargemode_config/phase_switch_delay": 5}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 68)

    def upgrade_datastore_68(self) -> None:
        def upgrade(topic: str, payload) -> None:
            if re.search("openWB/system/device/[0-9]+", topic) is not None:
                payload = decode_payload(payload)
                index = get_index(topic)
                if payload.get("type") == "discovergy":
                    for component_topic, component_payload in self.all_received_topics.items():
                        if re.search(f"openWB/system/device/{index}/component/[0-9]+/config",
                                     component_topic) is not None:
                            config_payload = decode_payload(component_payload)
                            if "info" not in config_payload:
                                config_payload.update({"info": {"manufacturer": None, "model": None}})
                                return {component_topic: config_payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 69)

    def upgrade_datastore_69(self) -> None:
        def upgrade(topic: str, payload) -> Optional[dict]:
            if (re.search("openWB/vehicle/template/charge_template/[0-9]+/chargemode/scheduled_charging/plans/[0-9]+",
                          topic) is not None or
                    re.search("openWB/vehicle/template/charge_template/[0-9]+/time_charging/plans/[0-9]+",
                              topic) is not None):
                payload = decode_payload(payload)
                payload["id"] = int(get_second_index(topic))
                return {topic: payload}
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 70)

    def upgrade_datastore_70(self) -> None:
        def upgrade(topic: str, payload) -> None:
            if re.search("openWB/vehicle/[0-9]+/soc_module/config", topic) is not None:
                payload = decode_payload(payload)
                # replace smarteq soc module by no_module
                if payload.get("type") == "smarteq":
                    payload = NO_MODULE
                Pub().pub(topic, payload)
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 71)

    def upgrade_datastore_71(self) -> None:
        def upgrade(topic: str, payload) -> None:
            if re.search("openWB/system/device/[0-9]+", topic) is not None:
                payload = decode_payload(payload)
                # update firmware of Sungrow
                if payload.get("type") == "sungrow":
                    if "firmware" not in payload["configuration"]:
                        payload["configuration"].update({"firmware": "v1"})
                    elif payload["configuration"].get("firmware") == "v111":
                        payload["configuration"]["firmware"] = "v1"
                    elif payload["configuration"].get("firmware") == "v112":
                        payload["configuration"]["firmware"] = "v2"
                Pub().pub(topic, payload)
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 72)

    def upgrade_datastore_72(self) -> None:
        def upgrade(topic: str, payload) -> None:
            if re.search("openWB/vehicle/[0-9]+/soc_module/config", topic) is not None:
                payload = decode_payload(payload)
                # replace bmw soc module by no_module
                if payload.get("type") == "bmw":
                    payload = NO_MODULE
                Pub().pub(topic, payload)
        self._loop_all_received_topics(upgrade)
        self.__update_topic("openWB/system/datastore_version", 73)
