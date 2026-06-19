from unittest.mock import Mock

import pytest

from control import data
from control.chargemode import Chargemode
from control.consumer.consumer import Consumer, WaitForStartStates
from control.consumer.consumer_data import ContinuousDeviceConfig
from helpermodules import timecheck


@pytest.fixture(autouse=True)
def mock_data() -> None:
    data.data_init(Mock())


@pytest.fixture
def consumer() -> Consumer:
    load = Consumer(1)
    load.data.usage = ContinuousDeviceConfig()
    load.data.config.min_current = 6
    return load


def test_wait_for_start_handler_runs_func_when_disabled(consumer: Consumer):
    consumer.data.usage.wait_for_start_active = False
    charging_func = Mock(return_value=(11, "ok", Chargemode.ECO_CHARGING, Chargemode.PV_CHARGING))

    required_current, message, mode, submode = consumer.wait_for_start_handler(charging_func)

    assert required_current == 11
    assert message == "ok"
    assert mode == Chargemode.ECO_CHARGING
    assert submode == Chargemode.PV_CHARGING
    charging_func.assert_called_once_with()


def test_wait_for_start_handler_start_signal_received(monkeypatch: pytest.MonkeyPatch, consumer: Consumer):
    consumer.data.usage.wait_for_start_active = True
    consumer.data.set.wait_for_start_test_running = True
    consumer.data.set.wait_for_start_signal_received = False
    monkeypatch.setattr(consumer, "_wait_for_start_signal", Mock(return_value=WaitForStartStates.START_SIGNAL_RECEIVED))
    charging_func = Mock(return_value=(9, "running", Chargemode.PV_CHARGING, Chargemode.PV_CHARGING))

    required_current, message, mode, submode = consumer.wait_for_start_handler(charging_func)

    assert required_current == 9
    assert message == "running"
    assert mode == Chargemode.PV_CHARGING
    assert submode == Chargemode.PV_CHARGING
    assert consumer.data.set.wait_for_start_signal_received is True
    assert consumer.data.set.wait_for_start_test_running is False
    charging_func.assert_called_once_with()


def test_wait_for_start_handler_starts_test_run(monkeypatch: pytest.MonkeyPatch, consumer: Consumer):
    consumer.data.usage.wait_for_start_active = True
    monkeypatch.setattr(consumer, "_wait_for_start_signal", Mock(return_value=WaitForStartStates.START_TEST_RUN))
    monkeypatch.setattr(timecheck, "create_timestamp", Mock(return_value=1000))

    required_current, message, mode, submode = consumer.wait_for_start_handler(Mock())

    assert required_current == 6
    assert message == consumer.WAIT_FOR_START_SIGNAL_TEST_RUN
    assert mode == Chargemode.INSTANT_CHARGING
    assert submode == Chargemode.INSTANT_CHARGING
    assert consumer.data.set.wait_for_start_test_running is True
    assert consumer.data.set.wait_for_start_last_test_timestamp == 1000


def test_wait_for_start_signal_wait_for_next_test_run(monkeypatch: pytest.MonkeyPatch, consumer: Consumer):
    consumer.data.usage.wait_for_start_active = True
    consumer.data.set.wait_for_start_last_test_timestamp = 780
    monkeypatch.setattr(
        consumer,
        "_wait_for_start_signal",
        Mock(return_value=WaitForStartStates.WAIT_FOR_NEXT_TEST_RUN),
    )
    monkeypatch.setattr(timecheck, "create_timestamp", Mock(return_value=800))

    required_current, message, mode, submode = consumer.wait_for_start_handler(Mock())

    assert required_current == 0
    assert message == consumer.WAIT_FOR_START_SIGNAL.format("59 Min. 40 Sek.")
    assert mode == Chargemode.STOP
    assert submode == Chargemode.STOP
    assert consumer.data.set.wait_for_start_test_running is False


@pytest.mark.parametrize(
    "signal_received,test_running,charge_state,now,last_test_timestamp,expected_state",
    [
        pytest.param(True, False, True, 0, 0, WaitForStartStates.START_SIGNAL_RECEIVED,
                     id="already-received"),
        pytest.param(False, True, True, 0, 0, WaitForStartStates.START_SIGNAL_RECEIVED,
                     id="charge-state-during-test-run"),
        pytest.param(False, True, False, 0, 0, WaitForStartStates.WAIT_FOR_NEXT_TEST_RUN,
                     id="test-run-finished-no-signal"),
        pytest.param(False, False, False, 5000, 500, WaitForStartStates.START_TEST_RUN,
                     id="pause-elapsed"),
        pytest.param(False, False, False, 1000, 500, WaitForStartStates.WAIT_FOR_NEXT_TEST_RUN,
                     id="pause-not-elapsed"),
    ],
)
def test_wait_for_start_signal_state_machine(
    monkeypatch: pytest.MonkeyPatch,
    consumer: Consumer,
    signal_received: bool,
    test_running: bool,
    charge_state: bool,
    now: int,
    last_test_timestamp: int,
    expected_state: WaitForStartStates,
):
    consumer.data.set.wait_for_start_signal_received = signal_received
    consumer.data.set.wait_for_start_test_running = test_running
    consumer.data.get.charge_state = charge_state
    consumer.data.set.wait_for_start_last_test_timestamp = last_test_timestamp
    monkeypatch.setattr(timecheck, "create_timestamp", Mock(return_value=now))

    state = consumer._wait_for_start_signal()

    assert state == expected_state
