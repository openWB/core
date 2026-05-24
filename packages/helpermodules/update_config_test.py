from unittest.mock import Mock, patch, mock_open
from helpermodules import update_config
import json
from pathlib import Path

import pytest
from helpermodules.update_config import UpdateConfig


ALL_RECEIVED_TOPICS = {
    'openWB/chargepoint/5/get/voltages': b'[230.2,230.2,230.2]',
    'openWB/chargepoint/3/get/state_str': b'"Keine Ladung, da kein Auto angesteckt ist."',
    'openWB/chargepoint/3/config': (b'{"name": "Standard-Ladepunkt", "type": "mqtt", "ev": 0, "template": 0,'
                                    b'"connected_phases": 3, "phase_1": 1, "auto_phase_switch_hw": false, '
                                    b'"control_pilot_interruption_hw": false, "id": 3, "connection_module": '
                                    b'{"type": "mqtt", "name": "MQTT-Ladepunkt", "configuration": {}}, '
                                    b'"power_module": {}}'),
    'openWB/chargepoint/get/power': b'0',
    'openWB/chargepoint/template/0': (b'{"autolock": {"active": false, "plans": {}, "wait_for_charging_end": false}, '
                                      b'"name": "Standard Ladepunkt-Profil" '
                                      b'"valid_tags": [], "id": 0}'),
    'openWB/optional/int_display/theme': b'"cards"'}


def test_remove_invalid_topics(mock_pub):
    # setup
    update_config = UpdateConfig()
    update_config.all_received_topics = ALL_RECEIVED_TOPICS

    # execution
    update_config._remove_invalid_topics()

    # evaluation
    assert len(mock_pub.method_calls) == 2
    assert mock_pub.method_calls[0][1][0] == 'openWB/chargepoint/5/get/voltages'
    assert mock_pub.method_calls[1][1][0] == 'openWB/optional/int_display/theme'


@pytest.mark.parametrize("index_test_template, expected_index", [
    pytest.param(0, [2, 1], id="IDs korrekt"),
    pytest.param(1, [0, 3], id="IDs gleich"),
    pytest.param(2, [], id="keine Pläne"),
])
def test_upgrade_datastore_94(index_test_template, expected_index):
    update_con = UpdateConfig()
    update_con.all_received_topics = {"openWB/command/max_id/charge_template_scheduled_plan": 2}
    with open(Path(__file__).resolve().parents[0]/"upgrade_datastore_94.json", "r") as f:
        test_data = f.read()
    update_con.all_received_topics.update(json.loads(test_data)[index_test_template])
    update_con.all_received_topics["openWB/system/datastore_version"] = list(range(93))

    update_con.upgrade_datastore_94()

    plan_ids = []
    for plan in update_con.all_received_topics["openWB/vehicle/template/charge_template/0"]["chargemode"][
            "scheduled_charging"]["plans"]:
        plan_ids.append(plan["id"])
    assert plan_ids == expected_index


@pytest.mark.parametrize("name", [
    "happy_path",
    "missing_prices_dict",
    "empty_entry"])
def test_upgrade_datastore_122(name, monkeypatch):
    if name == "happy_path":
        log_content = {
            "entries": [
                {
                    "prices": {}, "cp": {"cp1": {}}, "ev": {"ev1": {}}, "counter": {"counter1": {}},
                    "pv": {"pv1": {}}, "bat": {"bat1": {}}, "hc": {"all": {}}
                }
            ]
        }
        expected_content = {
            "entries": [
                {
                    "prices": {"fault_state": None}, "cp": {"cp1": {"fault_state": None}},
                    "ev": {"ev1": {"fault_state": None}}, "counter": {"counter1": {"fault_state": None}},
                    "pv": {"pv1": {"fault_state": None}}, "bat": {"bat1": {"fault_state": None}},
                    "hc": {"all": {"fault_state": None}}
                }
            ]
        }
    elif name == "missing_prices_dict":
        log_content = {
            "entries": [
                {
                    "cp": {"cp1": {}}, "ev": {"ev1": {}}, "counter": {"counter1": {}},
                    "pv": {"pv1": {}}, "bat": {"bat1": {}}, "hc": {"all": {}}
                }
            ]
        }
        expected_content = {
            "entries": [
                {
                    "cp": {"cp1": {"fault_state": None}},
                    "ev": {"ev1": {"fault_state": None}}, "counter": {"counter1": {"fault_state": None}},
                    "pv": {"pv1": {"fault_state": None}}, "bat": {"bat1": {"fault_state": None}},
                    "hc": {"all": {"fault_state": None}}
                }
            ]
        }
    elif name == "empty_entry":
        log_content = {"entries": []}
        expected_content = {"entries": []}
    # Arrange
    uc = UpdateConfig()
    uc.all_received_topics = {"openWB/system/datastore_version": []}

    mock_dump = Mock()
    monkeypatch.setattr(update_config.json, "dump", mock_dump)
    mock_glob = Mock(return_value=["dummy_path"])
    monkeypatch.setattr(update_config.Path, "glob", mock_glob)

    # Act
    with patch("builtins.open", mock_open(read_data=json.dumps(log_content))):
        uc.upgrade_datastore_122()

        # Assert
        assert mock_dump.call_args_list[0].args[0] == expected_content
        assert uc.all_received_topics["openWB/system/datastore_version"] == [122]
