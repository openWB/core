import json
import random
import threading
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from helpermodules import update_config
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
    mock_glob = Mock(return_value=[Path("20240512.json")])
    monkeypatch.setattr(update_config.Path, "glob", mock_glob)

    def immediate_thread(*args, **kwargs):
        thread = threading.Thread(*args, **kwargs)

        def immediate_start():
            target = kwargs.get("target")
            thread_args = kwargs.get("args", ())
            if target is not None:
                target(*thread_args)

        thread.start = immediate_start
        return thread

    monkeypatch.setattr(update_config.threading, "Thread", immediate_thread)

    # Act
    with patch("builtins.open", mock_open(read_data=json.dumps(log_content))):
        uc.upgrade_datastore_122()

        # Assert
        assert mock_dump.call_args_list[0].args[0] == expected_content
        assert uc.all_received_topics["openWB/system/datastore_version"] == [122]


@pytest.mark.parametrize(
    "folders",
    [
        pytest.param(
            {
                "daily_log": [
                    "20240501.json"
                ],
                "monthly_log": [
                    "202401.json"
                ],
            },
            id="single_file_in_each_log_folder",
        ),
        pytest.param(
            {
                "daily_log": [
                    "20240501.json", "20240502.json", "20240503.json", "20240504.json",
                    "20240505.json", "20240506.json", "20240507.json", "20240508.json",
                    "20240509.json", "20240510.json", "20240511.json", "20240512.json",
                    "20240513.json",
                ],
                "monthly_log": [
                    "202401.json", "202402.json", "202403.json", "202404.json",
                    "202405.json", "202406.json", "202407.json", "202408.json",
                    "202409.json", "202410.json", "202411.json", "202412.json",
                ],
            },
            id="multiple_files_in_log_folders",
        ),
    ],
)
def test_latest_file_processed_sync_rest_async(monkeypatch, folders):
    """Verify latest file per folder is processed synchronously and the rest in one async batch."""
    uc = UpdateConfig()
    uc.base_path = Path("/mock_base")
    uc.all_received_topics = {"openWB/system/datastore_version": []}

    shuffled_paths_by_folder = {}
    for folder_name, file_names in folders.items():
        shuffled_names = file_names[:]
        random.shuffle(shuffled_names)
        shuffled_paths_by_folder[folder_name] = [
            Path(f"/mock_base/data/{folder_name}/{file_name}")
            for file_name in shuffled_names
        ]

    def mock_glob(self, pattern):
        folder_name = self.name
        return shuffled_paths_by_folder.get(folder_name, [])

    monkeypatch.setattr(update_config.Path, "glob", mock_glob)
    monkeypatch.setattr(
        "builtins.open",
        mock_open(read_data=json.dumps({"entries": [{"prices": {}}]})),
    )

    thread_calls = []

    def capture_thread(*args, **kwargs):
        thread_calls.append(kwargs)
        return type("MockThread", (), {"start": lambda self: None})()

    monkeypatch.setattr(update_config.threading, "Thread", capture_thread)

    uc.upgrade_datastore_122()

    expected_remaining_count = (
        sum(len(file_names) for file_names in folders.values()) - len(folders)
    )
    if expected_remaining_count == 0:
        assert thread_calls == [], "No thread should be created when there are no remaining files to process"
        return

    remaining_files = thread_calls[0]["args"][0]
    assert len(remaining_files) == expected_remaining_count
    assert thread_calls[0].get("daemon") is True, "Thread should be created as daemon"

    expected_remaining = []
    for folder_name, file_names in folders.items():
        expected_remaining.extend(
            Path(f"/mock_base/data/{folder_name}/{file_name}")
            for file_name in sorted(file_names, reverse=True)[1:]
        )
    assert remaining_files == expected_remaining
