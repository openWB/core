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


def test_upgrade_datastore_124_adds_missing_odometer_pattern_for_json_soc_module():
    update_con = UpdateConfig()
    update_con.all_received_topics = {
        "openWB/system/datastore_version": list(range(124)),
        "openWB/vehicle/0/soc_module/config": {
            "type": "json",
            "configuration": {
                "url": "https://example.invalid/soc",
                "soc_pattern": ".soc",
            }
        },
        "openWB/vehicle/1/soc_module/config": {
            "type": "homeassistant",
            "configuration": {
                "url": "http://ha.local"
            }
        }
    }

    update_con.upgrade_datastore_124()

    json_config = update_con.all_received_topics["openWB/vehicle/0/soc_module/config"]["configuration"]
    assert "odometer_pattern" in json_config
    assert json_config["odometer_pattern"] is None

    ha_config = update_con.all_received_topics["openWB/vehicle/1/soc_module/config"]["configuration"]
    assert "odometer_pattern" not in ha_config


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


def test_upgrade_datastore_125_converts_only_tariff_prices_and_persists(mock_pub):
    uc = UpdateConfig()
    uc.all_received_topics = {
        "openWB/optional/ep/flexible_tariff/provider": {
            "type": "fixed_hours",
            "configuration": {
                "tariffs": [
                    {"price": 0.15},
                    {"price": 0.09},
                ],
                "default_price": 0.01,
            },
        },
        "openWB/system/datastore_version": [123],
    }

    uc.upgrade_datastore_125()

    provider = uc.all_received_topics["openWB/optional/ep/flexible_tariff/provider"]
    assert provider["configuration"]["tariffs"][0]["price"] == pytest.approx(0.00015)
    assert provider["configuration"]["tariffs"][1]["price"] == pytest.approx(0.00009)
    assert provider["configuration"]["default_price"] == pytest.approx(0.00001)
    assert uc.all_received_topics["openWB/system/datastore_version"] == [123, 125]

    updated_topics = [call.args[0] for call in mock_pub.pub.call_args_list]
    assert "openWB/optional/ep/flexible_tariff/provider" in updated_topics
    assert "openWB/system/datastore_version" in updated_topics


def test_upgrade_datastore_125_converts_energycharts_surcharge(mock_pub):
    uc = UpdateConfig()
    uc.all_received_topics = {
        "openWB/optional/ep/flexible_tariff/provider": {
            "type": "energycharts",
            "configuration": {
                "surcharge": 10,
            },
        },
        "openWB/system/datastore_version": [123],
    }

    uc.upgrade_datastore_125()

    provider = uc.all_received_topics["openWB/optional/ep/flexible_tariff/provider"]
    assert provider["configuration"]["surcharge"] == pytest.approx(0.0001)
    assert uc.all_received_topics["openWB/system/datastore_version"] == [123, 125]

    updated_topics = [call.args[0] for call in mock_pub.pub.call_args_list]
    assert "openWB/optional/ep/flexible_tariff/provider" in updated_topics


def test_upgrade_datastore_125_is_idempotent_for_already_converted_values(mock_pub):
    uc = UpdateConfig()
    uc.all_received_topics = {
        "openWB/optional/ep/flexible_tariff/provider": {
            "type": "energycharts",
            "configuration": {
                "surcharge": 0.00015,
            },
        },
        "openWB/optional/ep/grid_fee/provider": {
            "type": "fixed_hours",
            "configuration": {
                "tariffs": [
                    {"price": 0.00006},
                    {"price": 0.00099},
                ],
                "default_price": 0.00008,
            },
        },
        "openWB/system/datastore_version": [123, 124],
    }

    expected_flexible = json.loads(json.dumps(uc.all_received_topics["openWB/optional/ep/flexible_tariff/provider"]))
    expected_grid_fee = json.loads(json.dumps(uc.all_received_topics["openWB/optional/ep/grid_fee/provider"]))

    uc.upgrade_datastore_125()

    assert uc.all_received_topics["openWB/optional/ep/flexible_tariff/provider"] == expected_flexible
    assert uc.all_received_topics["openWB/optional/ep/grid_fee/provider"] == expected_grid_fee
    assert uc.all_received_topics["openWB/system/datastore_version"] == [123, 124, 125]
    assert mock_pub.pub.call_count == 1  # einmal publishen für Upgrade der Datastore-Version
