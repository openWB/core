from unittest.mock import Mock

import pytest

from control import data
from helpermodules import timecheck
from modules.common.abstract_device import AbstractDevice
from modules.common.component_state import ConsumerState, CounterState
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store._consumer import ConsumerValueStoreBroker, PurgeConsumerState


@pytest.fixture(autouse=True)
def mock_data() -> None:
    data.data_init(Mock())


def _extra_meter_consumer(counter_fault_state: FaultState, counter_state: CounterState):
    data.data.consumer_data["consumer1"] = Mock(data=Mock(extra_meter=9))
    counter_component = Mock(
        fault_state=counter_fault_state,
        store=Mock(delegate=Mock(delegate=Mock(state=counter_state))))
    counter_component.component_config.id = 9
    data.data.system_data["device0"] = Mock(spec=AbstractDevice, components={"component9": counter_component})
    return PurgeConsumerState(delegate=Mock(delegate=ConsumerValueStoreBroker(1)))


def test_extra_meter_shows_live_power_when_counter_healthy():
    # setup
    fault_state = FaultState(ComponentInfo(9, "Zähler", "counter"))
    counter_state = CounterState(power=1234, imported=100, exported=50, currents=[1, 2, 3], powers=[1, 2, 3])
    purge = _extra_meter_consumer(fault_state, counter_state)

    # execution
    purge.update()

    # evaluation
    assert purge.delegate.set.call_args.args[0].power == 1234


def test_extra_meter_zeroes_power_after_counter_sustained_error():
    # setup - Verbraucher selbst fehlerfrei, nur der Zähler zählt hier
    fault_state = FaultState(ComponentInfo(9, "Zähler", "counter"))
    fault_state.error("Fehler")
    fault_state.error_timestamp = timecheck.create_timestamp() - 61
    counter_state = CounterState(power=1234, imported=100, exported=50, currents=[1, 2, 3], powers=[1, 2, 3])
    purge = _extra_meter_consumer(fault_state, counter_state)

    # execution
    purge.update()

    # evaluation
    assert purge.delegate.set.call_args.args[0].power == 0
    # Zählerstände selbst bleiben unverändert - nur die Leistung wird genullt
    assert purge.delegate.set.call_args.args[0].imported == 100
    assert purge.delegate.set.call_args.args[0].exported == 50


def test_extra_meter_keeps_power_within_counter_grace_period():
    # setup
    fault_state = FaultState(ComponentInfo(9, "Zähler", "counter"))
    fault_state.error("Fehler")
    fault_state.error_timestamp = timecheck.create_timestamp() - 30
    counter_state = CounterState(power=1234, imported=100, exported=50, currents=[1, 2, 3], powers=[1, 2, 3])
    purge = _extra_meter_consumer(fault_state, counter_state)

    # execution
    purge.update()

    # evaluation
    assert purge.delegate.set.call_args.args[0].power == 1234


def test_no_extra_meter_just_delegates():
    # setup
    data.data.consumer_data["consumer1"] = Mock(data=Mock(extra_meter=None))
    delegate = Mock(delegate=ConsumerValueStoreBroker(1))
    purge = PurgeConsumerState(delegate=delegate)
    purge.set(ConsumerState(power=500))

    # execution
    purge.update()

    # evaluation
    delegate.update.assert_called_once()
