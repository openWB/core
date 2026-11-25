import pytest

from control.chargepoint.chargepoint import Chargepoint
from control.consumer.consumer import Consumer


@pytest.mark.parametrize(
    "currents, expected_consumer, expected_chargepoint",
    [
        ([0, 0, 0], 0, 0),
        ([0.1, 0, 0], 0, 0),
        ([0.25, 0, 0], 0.25, 0),
        ([0.25, 0.35, 0.05], 0.3, 0),
        ([0.25, 0.75, 0], 0.5, 0.75),
        ([6, 8, 0.05], 7, 7),
    ],
)
def test_mean_current_uses_load_specific_standby_threshold(currents, expected_consumer, expected_chargepoint):
    consumer = Consumer(1)
    chargepoint = Chargepoint(2, None)
    consumer.data.get.currents = currents
    chargepoint.data.get.currents = currents

    assert consumer.get_mean_current() == pytest.approx(expected_consumer)
    assert chargepoint.get_mean_current() == pytest.approx(expected_chargepoint)


@pytest.mark.parametrize("load", [Consumer(1), Chargepoint(2, None)])
def test_set_timestamp_charge_start_resets_timestamps_when_current_is_zero(load):
    load.data.control_parameter.timestamp_charge_start = 1000
    load.data.control_parameter.timestamp_last_cp_retry = 2000
    load.data.set.current = 0

    load.set_timestamp_charge_start()

    assert load.data.control_parameter.timestamp_charge_start is None
    assert load.data.control_parameter.timestamp_last_cp_retry is None


@pytest.mark.parametrize("load", [Consumer(1), Chargepoint(2, None)])
def test_set_timestamp_charge_start_keeps_timestamps_while_charging(load):
    load.data.control_parameter.timestamp_charge_start = 1000
    load.data.control_parameter.timestamp_last_cp_retry = 2000
    load.data.set.current = 6

    load.set_timestamp_charge_start()

    assert load.data.control_parameter.timestamp_charge_start == 1000
    assert load.data.control_parameter.timestamp_last_cp_retry == 2000


@pytest.mark.parametrize("load", [Consumer(1), Chargepoint(2, None)])
def test_set_timestamp_charge_start_resets_retry_timestamp_without_charge_start(load):
    load.data.control_parameter.timestamp_charge_start = None
    load.data.control_parameter.timestamp_last_cp_retry = 2000
    load.data.set.current = 0

    load.set_timestamp_charge_start()

    assert load.data.control_parameter.timestamp_last_cp_retry is None
