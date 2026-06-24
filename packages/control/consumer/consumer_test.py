from typing import Optional, Tuple
from unittest.mock import Mock

import pytest

from control import data
from control.chargemode import Chargemode
from control.consumer.consumer import Consumer
from control.consumer.consumer_data import ContinuousDeviceConfig, WaitForStartStates


@pytest.fixture(autouse=True)
def mock_data() -> None:
    data.data_init(Mock())


@pytest.fixture
def consumer() -> Consumer:
    load = Consumer(1)
    load.data.usage = ContinuousDeviceConfig()
    load.data.config.min_current = 6
    load.data.config.max_power = 2300
    load.data.config.connected_phases = 1
    load.data.get.voltages = [230]
    return load


@pytest.mark.parametrize(
    ("wait_for_start_active",
     "state", "charge_state",
     "func_result",
     "expected_result",
     "expected_state",
     "func_calls"),
    [
        pytest.param(
            False,
            WaitForStartStates.WAIT_FOR_DEVICE_START,
            False,
            (11, "ok", Chargemode.ECO_CHARGING, Chargemode.PV_CHARGING),
            (11, "ok", Chargemode.ECO_CHARGING, Chargemode.PV_CHARGING),
            WaitForStartStates.WAIT_FOR_DEVICE_START,
            1,
            id="wait-for-start-disabled-passthrough",
        ),
        pytest.param(
            True,
            WaitForStartStates.WAIT_FOR_DEVICE_START,
            True,
            (9, "running", Chargemode.PV_CHARGING, Chargemode.PV_CHARGING),
            (0, Consumer.WAIT_FOR_STOPPED_DEVICE, Chargemode.STOP, Chargemode.STOP),
            WaitForStartStates.WAIT_FOR_STOPPED_DEVICE,
            0,
            id="wait-for-device-start-charge-detected",
        ),
        pytest.param(
            True,
            WaitForStartStates.WAIT_FOR_DEVICE_START,
            False,
            (9, "running", Chargemode.PV_CHARGING, Chargemode.PV_CHARGING),
            (6, Consumer.WAIT_FOR_DEVICE_START, Chargemode.INSTANT_CHARGING, Chargemode.INSTANT_CHARGING),
            WaitForStartStates.WAIT_FOR_DEVICE_START,
            0,
            id="wait-for-device-start-no-charge",
        ),
        pytest.param(
            True,
            WaitForStartStates.WAIT_FOR_STOPPED_DEVICE,
            False,
            (8, "pv ok", Chargemode.PV_CHARGING, Chargemode.PV_CHARGING),
            (8, f"{Consumer.DEVICE_WAITING_FOR_START} pv ok", Chargemode.PV_CHARGING, Chargemode.PV_CHARGING),
            WaitForStartStates.DEVICE_WAITING_FOR_START,
            1,
            id="wait-for-stopped-device-started-waiting",
        ),
        pytest.param(
            True,
            WaitForStartStates.DEVICE_WAITING_FOR_START,
            True,
            (7, "started", Chargemode.ECO_CHARGING, Chargemode.INSTANT_CHARGING),
            (7, "started", Chargemode.ECO_CHARGING, Chargemode.INSTANT_CHARGING),
            WaitForStartStates.START_SIGNAL_RECEIVED,
            1,
            id="device-waiting-start-signal-received",
        ),
        pytest.param(
            True,
            WaitForStartStates.START_SIGNAL_RECEIVED,
            True,
            (10, "continue", Chargemode.PV_CHARGING, Chargemode.PV_CHARGING),
            (10, "continue", Chargemode.PV_CHARGING, Chargemode.PV_CHARGING),
            WaitForStartStates.START_SIGNAL_RECEIVED,
            1,
            id="start-signal-received-passthrough",
        ),
    ],
)
def test_wait_for_start_handler(
        consumer: Consumer,
        wait_for_start_active: bool,
        state: WaitForStartStates,
        charge_state: bool,
        func_result: Tuple[int, str, Chargemode, Optional[Chargemode]],
        expected_result: Tuple[int, str, Chargemode, Optional[Chargemode]],
        expected_state: WaitForStartStates,
        func_calls: int,
):
    # setup
    assert isinstance(consumer.data.usage, ContinuousDeviceConfig)
    consumer.data.usage.wait_for_start_active = wait_for_start_active
    consumer.data.set.wait_for_start_state = state
    consumer.data.get.charge_state = charge_state
    charging_func = Mock(return_value=func_result)

    # execution
    result = consumer.wait_for_start_handler(charging_func)

    # evaluation
    assert result == expected_result
    assert consumer.data.set.wait_for_start_state == expected_state
    assert charging_func.call_count == func_calls
