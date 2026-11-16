import json
from copy import deepcopy
from unittest.mock import Mock, call

import pytest

from control import data, optional
from control.chargemode import Chargemode
from control.consumer.consumer import Consumer
from control.consumer.consumer_data import ConsumerConfig, RfidReset
from control.consumer.usage import ConsumerUsage
from dataclass_utils import asdict, dataclass_from_dict
from helpermodules.subdata import SubData
from helpermodules.changed_values_handler import ChangedValuesHandler


@pytest.fixture
def consumer(monkeypatch):
    data.data_init(Mock())
    data.data.optional_data = optional.Optional()
    data.data.optional_data.data.rfid.active = True
    consumer = Consumer(1)
    consumer.module = Mock()
    consumer.data.module = Mock(type="mqtt")
    consumer.data.config.rfid_enabled = True
    consumer.data.config.valid_tags = ["AB??", "1234"]
    consumer.data.usage.type = ConsumerUsage.SUSPENDABLE_ONOFF
    consumer.data.get.voltages = [230] * 3
    consumer.data.set.switch_interval_elapsed = True
    return consumer


def test_clear_rfid_publishes_input_resets_through_changed_values_handler(consumer, mock_pub):
    consumer.data.get.rfid = "1234"
    consumer.data.get.rfid_timestamp = 1000
    consumer.data.set.rfid = "1234"
    consumer.data.set.rfid_timestamp = 1000
    previous = deepcopy(consumer.data)
    handler = ChangedValuesHandler(Mock())
    mock_pub.pub.reset_mock()

    consumer.clear_rfid()

    assert consumer.data.get.rfid is None
    assert consumer.data.get.rfid_timestamp is None
    assert consumer.data.set.rfid == "1234"
    assert consumer.data.set.rfid_timestamp == 1000
    consumer.module.clear_rfid.assert_called_once_with()
    mock_pub.pub.assert_not_called()

    handler._update_value("openWB/set/consumer/1/", previous, consumer.data)

    assert mock_pub.pub.call_args_list == [call("openWB/set/consumer/1/get/rfid", None),
                                           call("openWB/set/consumer/1/get/rfid_timestamp", None)]


@pytest.mark.parametrize("mode", list(RfidReset))
def test_rfid_reset_config_keeps_existing_mqtt_values(mode):
    config = dataclass_from_dict(ConsumerConfig, {"rfid_reset": mode.value})
    assert config.rfid_reset is mode
    assert asdict(config)["rfid_reset"] == mode.value

    config = ConsumerConfig()
    assert config.rfid_reset is RfidReset.AFTER_TIME
    subdata = SubData.__new__(SubData)
    subdata.set_json_payload_class(
        config, Mock(topic="openWB/consumer/1/config", payload=json.dumps({"rfid_reset": mode.value}).encode()))
    assert config.rfid_reset is mode


@pytest.mark.parametrize("timestamp, expected_timestamp, expected_tag", [
    (None, 1000, "1234"),
    (900, 900, "1234"),
    (600, None, None),
    (0, None, None),
])
def test_input_timestamp_sets_release_start_and_expiry(
        consumer, monkeypatch, timestamp, expected_timestamp, expected_tag):
    monkeypatch.setattr("control.consumer.rfid.timecheck.create_timestamp", Mock(return_value=1000))
    consumer.data.get.rfid = "1234"
    consumer.data.get.rfid_timestamp = timestamp

    consumer.update_rfid()

    assert consumer.data.set.rfid == expected_tag
    assert consumer.data.set.rfid_timestamp == expected_timestamp
    assert consumer.data.get.rfid is None
    assert consumer.data.get.rfid_timestamp is None
    consumer.module.clear_rfid.assert_called_once_with()


@pytest.mark.parametrize("tag", ["1234", "unknown"])
def test_module_input_is_cleared_after_tag_evaluation(consumer, tag):
    consumer.data.get.rfid = tag

    def check_evaluated_tag():
        assert consumer.data.get.rfid is None
        if tag == "1234":
            assert consumer.data.set.rfid == tag
        else:
            assert consumer.data.set.rfid is None
            assert "nicht zugeordnet" in consumer.data.get.state_str

    consumer.module.clear_rfid.side_effect = check_evaluated_tag
    consumer.update_rfid()
    consumer.module.clear_rfid.assert_called_once_with()
    consumer.update_rfid()
    consumer.module.clear_rfid.assert_called_once_with()


@pytest.mark.parametrize("mode", list(Chargemode))
def test_locked_consumer_overrides_modes_and_switch_interval(consumer, mode):
    consumer.data.usage.chargemode = mode
    consumer.data.usage.time_charging.active = True

    current, message, _, submode = consumer.get_parameter()

    assert current == 0
    assert submode == Chargemode.STOP
    assert "RFID" in message


def test_tag_matching_expiry_and_rescan(consumer, monkeypatch):
    clock = Mock(return_value=1000)
    monkeypatch.setattr("control.consumer.rfid.timecheck.create_timestamp", clock)
    consumer.data.get.rfid = "ab12"
    consumer.update_rfid()
    assert consumer.data.get.rfid is None
    assert consumer.get_parameter()[0] > 0

    clock.return_value = 1299
    consumer.data.get.rfid = "unknown"
    consumer.update_rfid()
    assert consumer.data.set.rfid == "ab12"
    assert "nicht zugeordnet" in consumer.data.get.state_str

    clock.return_value = 1300
    consumer.update_rfid()
    assert consumer.data.set.rfid is None
    assert consumer.get_parameter()[0] == 0

    consumer.data.get.rfid = "1234"
    consumer.update_rfid()
    assert consumer.data.set.rfid_timestamp == 1300
    assert consumer.get_parameter()[0] > 0


def test_power_end_timeout_waits_for_operation_and_restarts_after_pause(consumer, monkeypatch):
    clock = Mock(return_value=1000)
    monkeypatch.setattr("control.consumer.rfid.timecheck.create_timestamp", clock)
    consumer.data.config.rfid_reset = RfidReset.AFTER_POWER_END
    consumer.data.get.rfid = "1234"
    consumer.update_rfid()

    clock.return_value = 2000
    consumer.update_rfid()
    assert consumer.data.set.rfid == "1234"
    assert consumer.data.set.rfid_power_end is None

    consumer.data.get.charge_state = True
    consumer.update_rfid()
    consumer.data.get.charge_state = False
    consumer.update_rfid()
    assert consumer.data.set.rfid_power_end == 2000

    clock.return_value = 2299
    consumer.data.get.charge_state = True
    consumer.update_rfid()
    assert consumer.data.set.rfid_power_end is None

    clock.return_value = 2500
    consumer.data.get.charge_state = False
    consumer.update_rfid()
    clock.return_value = 2799
    consumer.update_rfid()
    assert consumer.data.set.rfid == "1234"
    clock.return_value = 2800
    consumer.update_rfid()
    assert consumer.data.set.rfid is None
    assert consumer.get_parameter()[0] == 0


@pytest.mark.parametrize("disabled", ["global", "consumer", "unsupported", "extra_meter"])
def test_inactive_identification_does_not_restrict_operation(consumer, disabled):
    if disabled == "global":
        data.data.optional_data.data.rfid.active = False
    elif disabled == "consumer":
        consumer.data.config.rfid_enabled = False
    elif disabled == "extra_meter":
        consumer.data.extra_meter = 2
    else:
        consumer.data.module.type = "shelly"
    consumer.data.set.rfid = "old"
    consumer.data.get.rfid = "1234"

    consumer.update_rfid()

    assert consumer.data.set.rfid is None
    assert consumer.get_parameter()[0] > 0


@pytest.mark.parametrize("extra_meter", [0, 2])
def test_switching_meter_disables_rfid_and_requires_new_authorization_on_return(consumer, extra_meter):
    consumer.data.get.rfid = "1234"
    consumer.update_rfid()
    assert consumer.rfid_required()
    assert consumer.data.set.rfid == "1234"

    consumer.data.extra_meter = extra_meter
    assert not consumer.rfid_required()
    consumer.update_rfid()
    assert consumer.data.set.rfid is None
    assert consumer.data.set.rfid_timestamp is None
    assert consumer.data.set.rfid_power_seen is False
    assert consumer.data.set.rfid_power_end is None
    assert consumer.get_parameter()[0] > 0

    consumer.data.extra_meter = None
    assert consumer.rfid_required()
    assert consumer.get_parameter()[0] == 0


@pytest.mark.parametrize("usage", [ConsumerUsage.METER_ONLY, ConsumerUsage.SELF_CONTROLLED])
@pytest.mark.parametrize("pending_tag", [None, "1234"])
def test_uncontrolled_usage_clears_rfid_and_requires_new_scan_on_return(consumer, usage, pending_tag):
    consumer.data.get.rfid = "1234"
    consumer.update_rfid()
    assert consumer.data.set.rfid == "1234"
    consumer.data.set.rfid_power_seen = True
    consumer.data.set.rfid_power_end = 1000
    consumer.module.clear_rfid.reset_mock()

    consumer.data.usage.type = usage
    consumer.data.get.rfid = pending_tag
    consumer.data.get.rfid_timestamp = 1000 if pending_tag else None
    assert not consumer.rfid_required()

    consumer.update()

    assert consumer.data.set.rfid is None
    assert consumer.data.set.rfid_timestamp is None
    assert consumer.data.set.rfid_power_seen is False
    assert consumer.data.set.rfid_power_end is None
    assert consumer.data.get.rfid is None
    assert consumer.data.get.rfid_timestamp is None
    if pending_tag:
        consumer.module.clear_rfid.assert_called_once_with()
    else:
        consumer.module.clear_rfid.assert_not_called()

    consumer.data.usage.type = ConsumerUsage.SUSPENDABLE_ONOFF
    assert consumer.rfid_required()
    assert consumer.get_parameter()[0] == 0

    consumer.data.get.rfid = "1234"
    consumer.update_rfid()
    assert consumer.get_parameter()[0] > 0
