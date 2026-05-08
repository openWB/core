import copy
from dataclasses import asdict
import datetime
import glob
import importlib
import json
import logging
from pathlib import Path
import re
import time
from typing import List, Optional
import asyncio
from paho.mqtt.client import Client as MqttClient, MQTTMessage

from control.limiting_value import LoadmanagementLimit
import dataclass_utils

from control.chargepoint.chargepoint_template import get_chargepoint_template_default
from helpermodules import timecheck
from helpermodules import hardware_configuration
from helpermodules import pub
from helpermodules.broker import BrokerClient
from helpermodules.abstract_plans import Limit
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
from control.ev.charge_template import EcoCharging, get_charge_template_default
from control.ev import ev
from control.ev.ev_template import EvTemplateData
from control.general import Prices, PvCharging
from control.optional_data import OcppConfig
from modules.common.abstract_vehicle import GeneralVehicleConfig
from modules.common.component_type import ComponentType
from modules.devices.sungrow.sungrow_sh.version import Version
from modules.display_themes.cards.config import CardsDisplayTheme
from modules.io_actions.controllable_consumers.ripple_control_receiver.config import RippleControlReceiverSetup
from modules.web_themes.koala.config import KoalaWebTheme
from modules.devices.good_we.good_we.version import GoodWeVersion

log = logging.getLogger(__name__)

NO_MODULE = {"type": None, "configuration": {}}


class UpdateConfig:

    DATASTORE_VERSION = 122

    valid_topic = [
        "^openWB/bat/config/bat_control_permitted$",
        "^openWB/bat/config/bat_control_activated$",
        "^openWB/bat/config/power_limit_mode$",
        "^openWB/bat/config/power_limit_condition$",
        "^openWB/bat/config/bat_control_min_soc$",
        "^openWB/bat/config/bat_control_max_soc$",
        "^openWB/bat/config/manual_mode$",
        "^openWB/bat/config/price_limit_activated$",
        "^openWB/bat/config/price_limit$",
        "^openWB/bat/config/price_charge_activated$",
        "^openWB/bat/config/charge_limit$",
        "^openWB/bat/[0-9]+/config/max_power$",
        "^openWB/bat/[0-9]+/get/max_charge_power$",
        "^openWB/bat/[0-9]+/get/max_discharge_power$",
        "^openWB/bat/[0-9]+/get/state_str$",

        "^openWB/bat/config/configured$",
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
        "^openWB/chargepoint/template/[0-9]+/autolock/[0-9]+$",  # OBSOLET seit 2.1.8
        "^openWB/chargepoint/[0-9]+/config$",
        "^openWB/chargepoint/[0-9]+/control_parameter/chargemode$",
        "^openWB/chargepoint/[0-9]+/control_parameter/current_plan$",
        "^openWB/chargepoint/[0-9]+/control_parameter/failed_phase_switches$",
        "^openWB/chargepoint/[0-9]+/control_parameter/imported_at_plan_start$",
        "^openWB/chargepoint/[0-9]+/control_parameter/imported_instant_charging$",
        "^openWB/chargepoint/[0-9]+/control_parameter/limit$",
        "^openWB/chargepoint/[0-9]+/control_parameter/min_current$",
        "^openWB/chargepoint/[0-9]+/control_parameter/phases$",
        "^openWB/chargepoint/[0-9]+/control_parameter/prio$",
        "^openWB/chargepoint/[0-9]+/control_parameter/required_current$",
        "^openWB/chargepoint/[0-9]+/control_parameter/required_currents$",
        "^openWB/chargepoint/[0-9]+/control_parameter/state$",
        "^openWB/chargepoint/[0-9]+/control_parameter/submode$",
        "^openWB/chargepoint/[0-9]+/control_parameter/template_phases$",
        "^openWB/chargepoint/[0-9]+/control_parameter/timestamp_charge_start$",
        "^openWB/chargepoint/[0-9]+/control_parameter/timestamp_chargemode_changed$",
        "^openWB/chargepoint/[0-9]+/control_parameter/timestamp_last_phase_switch$",
        "^openWB/chargepoint/[0-9]+/control_parameter/timestamp_switch_on_off$",
        "^openWB/chargepoint/[0-9]+/get/charge_state$",
        "^openWB/chargepoint/[0-9]+/get/currents$",
        "^openWB/chargepoint/[0-9]+/get/current_branch$",
        "^openWB/chargepoint/[0-9]+/get/current_commit$",
        "^openWB/chargepoint/[0-9]+/get/error_timestamp$",
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
        "^openWB/chargepoint/[0-9]+/get/version$",
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
        "^openWB/chargepoint/[0-9]+/set/charge_template$",
        "^openWB/chargepoint/[0-9]+/set/current$",
        "^openWB/chargepoint/[0-9]+/set/manual_lock$",
        "^openWB/chargepoint/[0-9]+/set/charge_state_prev$",
        "^openWB/chargepoint/[0-9]+/set/plug_state_prev$",
        "^openWB/chargepoint/[0-9]+/set/plug_time$",
        "^openWB/chargepoint/[0-9]+/set/rfid$",
        "^openWB/chargepoint/[0-9]+/set/log$",
        "^openWB/chargepoint/[0-9]+/set/phases_to_use$",
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
        "^openWB/command/max_id/io_action$",
        "^openWB/command/max_id/io_device$",
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

        "^openWB/general/allow_unencrypted_access$",
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
        "^openWB/general/temporary_charge_templates_active$",
        "^openWB/general/notifications/selected$",
        "^openWB/general/notifications/configuration$",
        "^openWB/general/notifications/start_charging$",
        "^openWB/general/notifications/stop_charging$",
        "^openWB/general/notifications/plug$",
        "^openWB/general/notifications/smart_home$",
        "^openWB/general/chargemode_config/unbalanced_load_limit$",
        "^openWB/general/chargemode_config/unbalanced_load$",
        "^openWB/general/chargemode_config/pv_charging/bat_mode$",
        "^openWB/general/chargemode_config/pv_charging/feed_in_yield$",
        "^openWB/general/chargemode_config/pv_charging/switch_on_threshold$",
        "^openWB/general/chargemode_config/pv_charging/switch_on_delay$",
        "^openWB/general/chargemode_config/pv_charging/switch_off_threshold$",
        "^openWB/general/chargemode_config/pv_charging/switch_off_delay$",
        "^openWB/general/chargemode_config/pv_charging/phase_switch_delay$",
        "^openWB/general/chargemode_config/pv_charging/control_range$",
        "^openWB/general/chargemode_config/pv_charging/min_bat_soc$",
        "^openWB/general/chargemode_config/pv_charging/max_bat_soc$",
        "^openWB/general/chargemode_config/pv_charging/bat_power_discharge$",
        "^openWB/general/chargemode_config/pv_charging/bat_power_discharge_active$",
        "^openWB/general/chargemode_config/pv_charging/bat_power_reserve$",
        "^openWB/general/chargemode_config/pv_charging/bat_power_reserve_active$",
        "^openWB/general/chargemode_config/pv_charging/retry_failed_phase_switches$",
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
        "^openWB/internal_chargepoint/[0-1]/get/charge_state$",
        "^openWB/internal_chargepoint/[0-1]/get/currents$",
        "^openWB/internal_chargepoint/[0-1]/get/current_branch$",
        "^openWB/internal_chargepoint/[0-1]/get/current_commit$",
        "^openWB/internal_chargepoint/[0-1]/get/error_timestamp$",
        "^openWB/internal_chargepoint/[0-1]/get/evse_current$",
        "^openWB/internal_chargepoint/[0-1]/get/fault_state$",
        "^openWB/internal_chargepoint/[0-1]/get/fault_str$",
        "^openWB/internal_chargepoint/[0-1]/get/frequency$",
        "^openWB/internal_chargepoint/[0-1]/get/max_evse_current$",
        "^openWB/internal_chargepoint/[0-1]/get/plug_state$",
        "^openWB/internal_chargepoint/[0-1]/get/phases_in_use$",
        "^openWB/internal_chargepoint/[0-1]/get/exported$",
        "^openWB/internal_chargepoint/[0-1]/get/imported$",
        "^openWB/internal_chargepoint/[0-1]/get/power$",
        "^openWB/internal_chargepoint/[0-1]/get/powers$",
        "^openWB/internal_chargepoint/[0-1]/get/power_factors$",
        "^openWB/internal_chargepoint/[0-1]/get/vehicle_id$",
        "^openWB/internal_chargepoint/[0-1]/get/version$",
        "^openWB/internal_chargepoint/[0-1]/get/voltages$",
        "^openWB/internal_chargepoint/[0-1]/get/serial_number$",
        "^openWB/internal_chargepoint/[0-1]/get/soc$",
        "^openWB/internal_chargepoint/[0-1]/get/soc_timestamp$",
        "^openWB/internal_chargepoint/[0-1]/get/simulation$",
        "^openWB/internal_chargepoint/[0-1]/get/state_str$",
        "^openWB/internal_chargepoint/[0-1]/get/rfid$",
        "^openWB/internal_chargepoint/[0-1]/get/rfid_timestamp$",

        "^openWB/io/action/[0-9]+/config$",
        "^openWB/io/action/[0-9]+/timestamp$",

        "^openWB/mqtt/bat/[0-9]+/get/power$",
        "^openWB/mqtt/bat/[0-9]+/get/soc$",
        "^openWB/mqtt/bat/[0-9]+/get/imported$",
        "^openWB/mqtt/bat/[0-9]+/get/exported$",
        "^openWB/mqtt/counter/[0-9]+/get/currents$",
        "^openWB/mqtt/counter/[0-9]+/get/imported$",
        "^openWB/mqtt/counter/[0-9]+/get/exported$",
        "^openWB/mqtt/counter/[0-9]+/get/power$",
        "^openWB/mqtt/counter/[0-9]+/get/frequency$",
        "^openWB/mqtt/counter/[0-9]+/get/power_factors$",
        "^openWB/mqtt/counter/[0-9]+/get/powers$",
        "^openWB/mqtt/counter/[0-9]+/get/voltages$",
        "^openWB/mqtt/inverter/[0-9]+/get/currents$",
        "^openWB/mqtt/inverter/[0-9]+/get/power$",
        "^openWB/mqtt/inverter/[0-9]+/get/exported$",
        "^openWB/mqtt/inverter/[0-9]+/get/dc_power$",
        "^openWB/mqtt/vehicle/[0-9]+/get/range$",
        "^openWB/mqtt/vehicle/[0-9]+/get/soc$",
        "^openWB/mqtt/vehicle/[0-9]+/get/soc_timestamp$",

        "^openWB/set/log/request",
        "^openWB/set/log/data",

        "^openWB/optional/ep/flexible_tariff/get/fault_state$",
        "^openWB/optional/ep/flexible_tariff/get/fault_str$",
        "^openWB/optional/ep/flexible_tariff/get/prices$",
        "^openWB/optional/ep/flexible_tariff/provider$",
        "^openWB/optional/ep/grid_fee/get/fault_state$",
        "^openWB/optional/ep/grid_fee/get/fault_str$",
        "^openWB/optional/ep/grid_fee/get/prices$",
        "^openWB/optional/ep/grid_fee/provider$",
        "^openWB/optional/int_display/active$",
        "^openWB/optional/int_display/detected$",
        "^openWB/optional/int_display/on_if_plugged_in$",
        "^openWB/optional/int_display/pin_active$",
        "^openWB/optional/int_display/pin_code$",
        "^openWB/optional/int_display/standby$",
        "^openWB/optional/int_display/rotation$",
        "^openWB/optional/int_display/theme$",
        "^openWB/optional/int_display/only_local_charge_points",
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
        "^openWB/vehicle/template/charge_template/[0-9]+/time_charging/plans/[0-9]+$",  # OBSOLET seit 2.1.8
        # OBSOLET seit 2.1.8
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
        "^openWB/system/backup_password$",
        "^openWB/system/configurable/chargepoints$",
        "^openWB/system/configurable/chargepoints_internal$",
        "^openWB/system/configurable/devices_components$",
        "^openWB/system/configurable/flexible_tariffs$",
        "^openWB/system/configurable/grid_fees$",
        "^openWB/system/configurable/display_themes$",
        "^openWB/system/configurable/io_actions$",
        "^openWB/system/configurable/io_devices$",
        "^openWB/system/configurable/monitoring$",
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
        "^openWB/system/hostname$",
        "^openWB/system/io/[0-9]+/config$",
        "^openWB/system/ip_address$",
        "^openWB/system/lastlivevaluesJson$",
        "^openWB/system/mqtt/bridge/[0-9]+$",
        "^openWB/system/mqtt/valid_partner_ids$",
        "^openWB/system/release_train$",
        "^openWB/system/secondary_auto_update$",
        "^openWB/system/security/user_management_active$",
        "^openWB/system/security/access_allowed$",
        "^openWB/system/security/access/Settings$",
        "^openWB/system/security/access/Status$",
        "^openWB/system/security/access/ChargeLog$",
        "^openWB/system/security/access/Chart$",
        "^openWB/system/security/access/GeneralConfiguration$",
        "^openWB/system/security/access/DisplayConfiguration$",
        "^openWB/system/security/access/IdentificationConfiguration$",
        "^openWB/system/security/access/GeneralChargeConfiguration$",
        "^openWB/system/security/access/SurplusChargeConfiguration$",
        "^openWB/system/security/access/ActiveBatControlConfiguration$",
        "^openWB/system/security/access/HardwareInstallation$",
        "^openWB/system/security/access/LoadManagementConfiguration$",
        "^openWB/system/security/access/ChargePointInstallation$",
        "^openWB/system/security/access/VehicleConfiguration$",
        "^openWB/system/security/access/IoConfiguration$",
        "^openWB/system/security/access/LegacySmartHomeConfiguration$",
        "^openWB/system/security/access/InstallAssistant$",
        "^openWB/system/security/access/CloudConfiguration$",
        "^openWB/system/security/access/MqttBridgeConfiguration$",
        "^openWB/system/security/access/DebugConfiguration$",
        "^openWB/system/security/access/Support$",
        "^openWB/system/security/access/DataManagement$",
        "^openWB/system/security/access/SecurityConfiguration$",
        "^openWB/system/security/access/SystemConfiguration$",
        "^openWB/system/security/access/LegalSettings$",
        "^openWB/system/time$",
        "^openWB/system/update_in_progress$",
        "^openWB/system/usage_terms_acknowledged$",
        "^openWB/system/version$",
    ]
    default_topic = (
        ("openWB/bat/config/bat_control_permitted", False),
        ("openWB/bat/config/bat_control_activated", False),
        ("openWB/bat/config/power_limit_mode", "mode_no_discharge"),
        ("openWB/bat/config/power_limit_condition", "vehicle_charging"),
        ("openWB/bat/config/bat_control_min_soc", 5),
        ("openWB/bat/config/bat_control_max_soc", 90),
        ("openWB/bat/config/manual_mode", "manual_disable"),
        ("openWB/bat/config/price_limit_activated", False),
        ("openWB/bat/config/price_limit$", 0.3),
        ("openWB/bat/config/price_charge_activated", False),
        ("openWB/bat/config/charge_limit$", 0.3),
        ("openWB/bat/config/configured", False),
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
        ("openWB/vehicle/0/charge_template", ev.Ev(0).charge_template.data.id),
        ("openWB/vehicle/0/soc_module/config", NO_MODULE),
        ("openWB/vehicle/0/soc_module/general_config", dataclass_utils.asdict(GeneralVehicleConfig())),
        ("openWB/vehicle/0/ev_template", ev.Ev(0).ev_template.data.id),
        ("openWB/vehicle/0/tag_id", ev.Ev(0).data.tag_id),
        ("openWB/vehicle/0/get/soc", ev.Ev(0).data.get.soc),
        ("openWB/vehicle/template/ev_template/0", asdict(EvTemplateData(name="Standard-Fahrzeug-Profil",
                                                                        min_current=10))),
        ("openWB/vehicle/template/charge_template/0", get_charge_template_default()),
        ("openWB/general/allow_unencrypted_access", True),
        ("openWB/general/charge_log_data_config", get_default_charge_log_columns()),
        ("openWB/general/chargemode_config/pv_charging/bat_mode", BatConsiderationMode.EV_MODE.value),
        ("openWB/general/chargemode_config/pv_charging/bat_power_discharge", 1000),
        ("openWB/general/chargemode_config/pv_charging/bat_power_discharge_active", True),
        ("openWB/general/chargemode_config/pv_charging/min_bat_soc", 50),
        ("openWB/general/chargemode_config/pv_charging/max_bat_soc", 70),
        ("openWB/general/chargemode_config/pv_charging/bat_power_reserve", 200),
        ("openWB/general/chargemode_config/pv_charging/bat_power_reserve_active", True),
        ("openWB/general/chargemode_config/pv_charging/control_range", [0, 230]),
        ("openWB/general/chargemode_config/pv_charging/switch_off_threshold", 0),
        ("openWB/general/chargemode_config/pv_charging/switch_off_delay", 60),
        ("openWB/general/chargemode_config/pv_charging/switch_on_delay", 30),
        ("openWB/general/chargemode_config/pv_charging/switch_on_threshold", 1500),
        ("openWB/general/chargemode_config/pv_charging/feed_in_yield", 0),
        ("openWB/general/chargemode_config/pv_charging/phase_switch_delay", 7),
        ("openWB/general/chargemode_config/pv_charging/retry_failed_phase_switches",
         PvCharging().retry_failed_phase_switches),
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
        ("openWB/general/temporary_charge_templates_active", False),
        ("openWB/general/web_theme", dataclass_utils.asdict(KoalaWebTheme())),
        ("openWB/graph/config/duration", 120),
        ("openWB/internal_chargepoint/0/data/parent_cp", None),
        ("openWB/internal_chargepoint/1/data/parent_cp", None),
        ("openWB/optional/ep/flexible_tariff/provider", NO_MODULE),
        ("openWB/optional/ep/grid_fee/provider", NO_MODULE),
        ("openWB/optional/int_display/active", True),
        ("openWB/optional/int_display/detected", True),
        ("openWB/optional/int_display/on_if_plugged_in", True),
        ("openWB/optional/int_display/pin_active", False),
        ("openWB/optional/int_display/pin_code", "0000"),
        ("openWB/optional/int_display/standby", 60),
        ("openWB/optional/int_display/rotation", 0),
        ("openWB/optional/int_display/theme", dataclass_utils.asdict(CardsDisplayTheme())),
        ("openWB/optional/int_display/only_local_charge_points", False),
        ("openWB/optional/monitoring/config", NO_MODULE),
        ("openWB/optional/ocpp/config", dataclass_utils.asdict(OcppConfig())),
        ("openWB/optional/rfid/active", False),
        ("openWB/system/backup_password", None),
        ("openWB/system/backup_cloud/config", NO_MODULE),
        ("openWB/system/backup_cloud/backup_before_update", True),
        ("openWB/system/current_branch", None),
        ("openWB/system/current_commit", None),
        ("openWB/system/installAssistantDone", False),
        ("openWB/system/dataprotection_acknowledged", False),
        ("openWB/system/datastore_version", list(range(DATASTORE_VERSION))),
        ("openWB/system/usage_terms_acknowledged", False),
        ("openWB/system/debug_level", 30),
        ("openWB/system/device/module_update_completed", True),
        ("openWB/system/hostname", "unknown"),
        ("openWB/system/ip_address", "unknown"),
        ("openWB/system/mqtt/valid_partner_ids", []),
        ("openWB/system/release_train", "master"),
        ("openWB/system/secondary_auto_update", True),
        ("openWB/system/serial_number", get_serial_number()),
        ("openWB/system/security/user_management_active", False),
        # the following topics in openWB/system/security/ must default to True!
        # ACLs will restrict access to this topics if user management is active so that the UI can distinguish
        # between "no access" (no topic received) and "access" (topic received)
        ("openWB/system/security/access_allowed", True),
        ("openWB/system/security/access/Settings", True),
        ("openWB/system/security/access/Status", True),
        ("openWB/system/security/access/ChargeLog", True),
        ("openWB/system/security/access/Chart", True),
        ("openWB/system/security/access/GeneralConfiguration", True),
        ("openWB/system/security/access/DisplayConfiguration", True),
        ("openWB/system/security/access/IdentificationConfiguration", True),
        ("openWB/system/security/access/GeneralChargeConfiguration", True),
        ("openWB/system/security/access/SurplusChargeConfiguration", True),
        ("openWB/system/security/access/ActiveBatControlConfiguration", True),
        ("openWB/system/security/access/HardwareInstallation", True),
        ("openWB/system/security/access/LoadManagementConfiguration", True),
        ("openWB/system/security/access/ChargePointInstallation", True),
        ("openWB/system/security/access/VehicleConfiguration", True),
        ("openWB/system/security/access/IoConfiguration", True),
        ("openWB/system/security/access/LegacySmartHomeConfiguration", True),
        ("openWB/system/security/access/InstallAssistant", True),
        ("openWB/system/security/access/CloudConfiguration", True),
        ("openWB/system/security/access/MqttBridgeConfiguration", True),
        ("openWB/system/security/access/DebugConfiguration", True),
        ("openWB/system/security/access/Support", True),
        ("openWB/system/security/access/DataManagement", True),
        ("openWB/system/security/access/SecurityConfiguration", True),
        ("openWB/system/security/access/SystemConfiguration", True),
        ("openWB/system/security/access/LegalSettings", True),
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
        BrokerClient("update-config", self.on_connect, self.on_message).start_finite_loop()
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
            self.all_received_topics[topic] = copy.deepcopy(payload)

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
        """ datastore_version ist eine Liste mit allen durchgeführten datastore-Upgrades, damit bei Patch-Versionen
        einzelne Upgrades übersprungen werden können und bei einem anschließenden Major-Upgrade alle fehlenden Upgrades
        durchgeführt werden."""
        datastore_versions = decode_payload(self.all_received_topics.get("openWB/system/datastore_version"))
        if datastore_versions is None or isinstance(datastore_versions, int):
            datastore_versions = list(range(datastore_versions or self.DATASTORE_VERSION+1))
            self.__update_topic("openWB/system/datastore_version", datastore_versions)
        log.debug(f"current datastore version: {datastore_versions}")
        log.debug(f"target datastore version: {self.DATASTORE_VERSION}")
        for version in list(range(self.DATASTORE_VERSION+1)):
            try:
                if version not in datastore_versions:
                    log.debug(f"upgrading datastore version '{version}'")
                    getattr(self, f"upgrade_datastore_{version}")()
            except AttributeError:
                log.error(f"missing upgrade function! '{version}'")
            except Exception:
                log.exception("Fehler bei der Aktualisierung des Brokers.")
                pub_system_message(
                    {}, "Fehler bei der Aktualisierung der Konfiguration des Brokers.", MessageType.ERROR)

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

    def _append_datastore_version(self, version: int) -> None:
        datastore_versions = decode_payload(self.all_received_topics.get("openWB/system/datastore_version"))
        if version not in datastore_versions:
            datastore_versions.append(version)
            self.__update_topic("openWB/system/datastore_version", datastore_versions)

    # ... [upgrade_datastore_0 through upgrade_datastore_121 remain unchanged] ...

    def upgrade_datastore_122(self) -> None:
        """Process log files with fault_state updates. Latest file first (synchronous),
        then process remaining files asynchronously."""
        
        def process_file(file_path: Path) -> bool:
            """Process a single file and return True if successful, False otherwise."""
            try:
                with open(file_path, "r+") as jsonFile:
                    content = json.load(jsonFile)
                    for entry in content["entries"]:
                        if entry.get("prices") is not None and entry["prices"].get("fault_state") is None:
                            entry["prices"]["fault_state"] = None
                        for cp in entry.get("cp", {}).values():
                            if cp.get("fault_state") is None:
                                cp["fault_state"] = None
                        for ev_data in entry.get("ev", {}).values():
                            if ev_data.get("fault_state") is None:
                                ev_data["fault_state"] = None
                        for counter in entry.get("counter", {}).values():
                            if counter.get("fault_state") is None:
                                counter["fault_state"] = None
                        for pv in entry.get("pv", {}).values():
                            if pv.get("fault_state") is None:
                                pv["fault_state"] = None
                        for bat in entry.get("bat", {}).values():
                            if bat.get("fault_state") is None:
                                bat["fault_state"] = None
                        if entry.get("hc") is not None and entry["hc"].get("all") is not None:
                            if entry["hc"]["all"].get("fault_state") is None:
                                entry["hc"]["all"]["fault_state"] = None

                    jsonFile.seek(0)
                    json.dump(content, jsonFile)
                    jsonFile.truncate()
                    log.debug(f"Format der Logdatei '{file_path}' aktualisiert.")
                    return True
            except FileNotFoundError:
                pass
            except Exception:
                log.exception(f"Logdatei '{file_path}' konnte nicht konvertiert werden.")
            return False

        async def process_files_async(file_paths: List[Path]) -> None:
            """Asynchronously process remaining files."""
            for file_path in file_paths:
                process_file(file_path)
                await asyncio.sleep(0)  # Yield control to event loop

        for folder in ("daily_log", "monthly_log"):
            folder_path = self.base_path / "data" / folder
            # Get all JSON files and sort by modification time (newest first)
            path_list = sorted(
                folder_path.glob('**/*.json'),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            if not path_list:
                continue

            # Process latest file synchronously
            latest_file = path_list[0]
            log.debug(f"Processing latest file synchronously: {latest_file}")
            process_file(latest_file)

            # Start async task to process remaining files
            if len(path_list) > 1:
                remaining_files = path_list[1:]
                log.debug(f"Starting async task to process {len(remaining_files)} remaining files")
                try:
                    asyncio.create_task(process_files_async(remaining_files))
                except RuntimeError:
                    # If no event loop is running, process remaining files synchronously
                    log.debug("No event loop running, processing remaining files synchronously")
                    for file_path in remaining_files:
                        process_file(file_path)

        self._append_datastore_version(122)
