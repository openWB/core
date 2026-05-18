import json
from pathlib import Path
import re

from helpermodules.update_config import UpdateConfig
from test_utils.test_environment import running_on_github


def _get_data_path() -> Path:
    if running_on_github():
        return Path("/home/runner/work/core/core/data")
    else:
        return Path(__file__).resolve().parents[3]/"data"


DEFAULT_DYNAMIC_SECURITY_PATH = _get_data_path()/"config/mosquitto/public/default-dynamic-security.json"
ROLE_TEMPLATES_PATH = _get_data_path()/"config/mosquitto/public/role-templates.json"


INTERNAL_TOPICS = ['openWB/bat/set/charging_power_left',
                   'openWB/bat/set/regulate_up',
                   'openWB/bat/+/set/power_limit',
                   'openWB/command/max_id/autolock_plan',
                   'openWB/command/max_id/charge_template',
                   'openWB/command/max_id/charge_template_scheduled_plan',
                   'openWB/command/max_id/charge_template_time_charging_plan',
                   'openWB/command/max_id/chargepoint_template',
                   'openWB/command/max_id/device',
                   'openWB/command/max_id/ev_template',
                   'openWB/command/max_id/hierarchy',
                   'openWB/command/max_id/io_action',
                   'openWB/command/max_id/io_device',
                   'openWB/command/max_id/mqtt_bridge',
                   'openWB/command/max_id/vehicle',
                   'openWB/command/[A-Za-z0-9_]+/error',
                   'openWB/command/todo',
                   'openWB/counter/set/disengageable_smarthome_power',
                   'openWB/counter/set/invalid_home_consumption',
                   'openWB/counter/set/simulation',
                   'openWB/counter/+/set/consumption_left',
                   'openWB/counter/+/set/error_timer',
                   'openWB/counter/+/set/released_surplus',
                   'openWB/counter/+/set/reserved_surplus',
                   'openWB/general/grid_protection_active',
                   'openWB/general/grid_protection_timestamp',
                   'openWB/general/grid_protection_random_stop',
                   'openWB/general/price_kwh',  # obsolet topic
                   'openWB/graph/config/duration',
                   'openWB/internal_chargepoint/+/data/cp_interruption_duration',
                   'openWB/internal_chargepoint/+/data/set_current',
                   'openWB/internal_chargepoint/+/data/phases_to_use',
                   'openWB/internal_chargepoint/+/get/charge_state',
                   'openWB/internal_chargepoint/+/get/currents',
                   'openWB/internal_chargepoint/+/get/current_branch',
                   'openWB/internal_chargepoint/+/get/current_commit',
                   'openWB/internal_chargepoint/+/get/error_timestamp',
                   'openWB/internal_chargepoint/+/get/evse_current',
                   'openWB/internal_chargepoint/+/get/fault_state',
                   'openWB/internal_chargepoint/+/get/fault_str',
                   'openWB/internal_chargepoint/+/get/frequency',
                   'openWB/internal_chargepoint/+/get/max_evse_current',
                   'openWB/internal_chargepoint/+/get/plug_state',
                   'openWB/internal_chargepoint/+/get/phases_in_use',
                   'openWB/internal_chargepoint/+/get/exported',
                   'openWB/internal_chargepoint/+/get/imported',
                   'openWB/internal_chargepoint/+/get/power',
                   'openWB/internal_chargepoint/+/get/powers',
                   'openWB/internal_chargepoint/+/get/power_factors',
                   'openWB/internal_chargepoint/+/get/vehicle_id',
                   'openWB/internal_chargepoint/+/get/version',
                   'openWB/internal_chargepoint/+/get/voltages',
                   'openWB/internal_chargepoint/+/get/serial_number',
                   'openWB/internal_chargepoint/+/get/soc',
                   'openWB/internal_chargepoint/+/get/soc_timestamp',
                   'openWB/internal_chargepoint/+/get/simulation',
                   'openWB/internal_chargepoint/+/get/state_str',
                   'openWB/internal_chargepoint/+/get/rfid',
                   'openWB/internal_chargepoint/+/get/rfid_timestamp',
                   # abgesehen vom Fahrzeug können mqtt get-Topics bei aktiver BV nur gepublished werden
                   'openWB/mqtt/bat/+/get/power',
                   'openWB/mqtt/bat/+/get/soc',
                   'openWB/mqtt/bat/+/get/imported',
                   'openWB/mqtt/bat/+/get/exported',
                   'openWB/mqtt/counter/+/get/currents',
                   'openWB/mqtt/counter/+/get/imported',
                   'openWB/mqtt/counter/+/get/exported',
                   'openWB/mqtt/counter/+/get/power',
                   'openWB/mqtt/counter/+/get/frequency',
                   'openWB/mqtt/counter/+/get/power_factors',
                   'openWB/mqtt/counter/+/get/powers',
                   'openWB/mqtt/counter/+/get/voltages',
                   'openWB/mqtt/inverter/+/get/currents',
                   'openWB/mqtt/inverter/+/get/power',
                   'openWB/mqtt/inverter/+/get/exported',
                   'openWB/mqtt/inverter/+/get/dc_power',
                   'openWB/set/log/request',
                   'openWB/set/log/data',
                   'openWB/optional/int_display/detected',
                   'openWB/optional/int_display/pin_active',
                   'openWB/optional/int_display/pin_code',
                   'openWB/system/datastore_version',
                   'openWB/system/device/+/component/+/simulation',
                   'openWB/system/device/+/component/+/simulation/power_present',
                   'openWB/system/device/+/component/+/simulation/present_exported',
                   'openWB/system/device/+/component/+/simulation/present_imported',
                   'openWB/system/device/+/component/+/simulation/timestamp_present',
                   'openWB/system/device/module_update_completed',
                   'openWB/system/hostname',
                   'openWB/system/lastlivevaluesJson',
                   'openWB/system/release_train']

NOT_PERSISTENT_TOPICS = ['openWB/system/messages/[^/]+',
                         'openWB/system/messages/.*',
                         'openWB/command/[^/]+/messages/[^/]+',
                         'openWB/command/[^/]+/messages/.*',
                         'openWB/system/serial_number',
                         'openWB/system/mac_address',
                         'openWB/optional/dc_charging',
                         'others/.*',
                         '$CONTROL/dynamic-security/.*',
                         '$SYS/.*',
                         'openWB/simpleAPI/set/.*',
                         'openWB-remote/.*',
                         'openWB/log/[^/]+/data',
                         'openWB/log/daily/.*',
                         'openWB/log/monthly/.*',
                         'openWB/log/yearly/.*',
                         '$CONTROL/dynamic-security/v1',
                         '$CONTROL/dynamic-security/v1/response',
                         ]


def test_valid_topics_vs_role_topics():
    def parse_acl_topic_to_regex(acl_topic):
        if "openWB/set" not in acl_topic and "#" != acl_topic and "openWB/#" != acl_topic:
            # convert mqtt topic pattern to regex pattern
            topic_regex = acl_topic.replace("+", "[^/]+").replace("#", ".*").replace("<id>", "[^/]+")
            return topic_regex
        return None
    # setup
    valid_topics = UpdateConfig.valid_topic
    for i, valid_topic in enumerate(valid_topics):
        if valid_topic.startswith("^"):
            valid_topic = valid_topic[1:]
        if valid_topic.endswith("$"):
            valid_topic = valid_topic[:-1]
        valid_topic = re.sub(r"\[0-9]\+", "+", valid_topic)
        valid_topic = re.sub(r"\[0-1]", "+", valid_topic)
        valid_topic = re.sub(r"\[0-9]", "+", valid_topic)
        valid_topics[i] = valid_topic

    with open(DEFAULT_DYNAMIC_SECURITY_PATH, "r") as f:
        security = json.load(f)
    role_topics = []
    for role in security.get("roles", []):
        for acl in role.get("acls", []):
            if "topic" in acl:
                topic_regex = parse_acl_topic_to_regex(acl["topic"])
                if topic_regex:
                    role_topics.append(topic_regex)
    with open(ROLE_TEMPLATES_PATH, "r") as f:
        roles = json.load(f)
    for role in roles:
        for acl in role.get("acls", []):
            if "topic" in acl:
                topic_regex = parse_acl_topic_to_regex(acl["topic"])
                if topic_regex:
                    role_topics.append(topic_regex)
    # execution
    # prüfen, ob alle valid_topics in den role_topics vorkommen, damit neue Topics nicht in der BV vergessen werden
    missing_valid_topic = []
    for valid_topic in valid_topics:
        found = False
        for role_topic in role_topics:
            if re.fullmatch(role_topic, valid_topic) or valid_topic in INTERNAL_TOPICS:
                found = True
                break
        if not found:
            missing_valid_topic.append(valid_topic)
    # prüfen, ob alle role_topics in den valid_topics vorkommen, damit keine ungültigen Topics in der BV sind
    missing_role_topic = []
    for role_topic in role_topics:
        found = False
        for valid_topic in valid_topics:
            if re.fullmatch(role_topic, valid_topic) or role_topic in NOT_PERSISTENT_TOPICS:
                found = True
                break
        if not found:
            missing_role_topic.append(role_topic)

    # assertion
    assert len(missing_valid_topic) == 0, f"Fehlende Topics in der Benutzerverwaltung: {missing_valid_topic}"
    assert len(missing_role_topic) == 0, f"Obsolete Topics in der Benutzerverwaltung: {missing_role_topic}"
