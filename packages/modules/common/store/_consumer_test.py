from unittest.mock import Mock

import pytest

from control import data
from helpermodules import timecheck
from modules.common.abstract_device import AbstractDevice
from modules.common.component_state import ConsumerState, CounterState
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.fault_state_level import FaultStateLevel
from modules.common.store import _consumer
from modules.common.store._consumer import ConsumerValueStoreBroker, PurgeConsumerState


@pytest.fixture(autouse=True)
def mock_data() -> None:
    data.data_init(Mock())


def _extra_meter_consumer(counter_fault_state: FaultState, counter_state: CounterState):
    data.data.consumer_data["consumer1"] = Mock(
        data=Mock(extra_meter=9),
        module=Mock(fault_state=FaultState(ComponentInfo(1, "Verbraucher", "consumer"))))
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
    # Die Leistung wurde bereits vom gemeinsamen Zähler-Store genullt.
    counter_state = CounterState(power=0, imported=100, exported=50, currents=[1, 2, 3], powers=[1, 2, 3])
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


@pytest.mark.parametrize("consumer_fault", list(FaultStateLevel))
@pytest.mark.parametrize("counter_fault", list(FaultStateLevel))
def test_extra_meter_forwards_fault_only_when_consumer_module_healthy(consumer_fault, counter_fault, mock_pub):
    fault_state = FaultState(ComponentInfo(9, "Zähler", "counter"))
    fault_state.fault_state = counter_fault
    fault_state.fault_str = "Zählerstatus"
    purge = _extra_meter_consumer(fault_state, CounterState(power=1234))
    data.data.consumer_data["consumer1"].module.fault_state.fault_state = consumer_fault
    data.data.consumer_data["consumer1"].module.fault_state.fault_str = "Verbraucherstatus"

    consumer_fault_state = data.data.consumer_data["consumer1"].module.fault_state
    with SingleComponentUpdateContext(consumer_fault_state, update_always=False):
        purge.update()

    expected_state = counter_fault if consumer_fault == FaultStateLevel.NO_ERROR else consumer_fault
    expected_str = "Zählerstatus" if consumer_fault == FaultStateLevel.NO_ERROR else "Verbraucherstatus"
    if consumer_fault == FaultStateLevel.NO_ERROR and counter_fault != FaultStateLevel.NO_ERROR:
        expected_str = f"Verknüpfter Zähler: {fault_state.fault_str}"
    assert consumer_fault_state.fault_state == expected_state
    assert consumer_fault_state.fault_str == expected_str
    assert fault_state.fault_str == "Zählerstatus"
    if expected_state != FaultStateLevel.NO_ERROR:
        mock_pub.pub.assert_any_call("openWB/set/consumer/1/get/fault_state", expected_state.value)
        mock_pub.pub.assert_any_call("openWB/set/consumer/1/get/fault_str", expected_str)


def test_extra_meter_clears_forwarded_fault_after_counter_recovers(mock_pub):
    fault_state = FaultState(ComponentInfo(9, "Zähler", "counter"))
    fault_state.error("Zähler nicht erreichbar")
    purge = _extra_meter_consumer(fault_state, CounterState(power=1234))
    consumer_fault_state = data.data.consumer_data["consumer1"].module.fault_state
    with SingleComponentUpdateContext(consumer_fault_state, update_always=False):
        purge.update()
    mock_pub.pub.reset_mock()

    fault_state.no_error()
    # Der nächste erfolgreiche Modulabruf setzt den eigenen Fehlerstatus regulär zurück.
    with SingleComponentUpdateContext(consumer_fault_state):
        pass
    with SingleComponentUpdateContext(consumer_fault_state, update_always=False):
        purge.update()

    assert consumer_fault_state.fault_state == FaultStateLevel.NO_ERROR
    mock_pub.pub.assert_any_call("openWB/set/consumer/1/get/fault_state", 0)
    mock_pub.pub.assert_any_call("openWB/set/consumer/1/get/fault_str", fault_state.fault_str)


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


def test_zero_power_on_sustained_error_without_prior_read_still_publishes():
    # setup - noch nie erfolgreich gelesen, aber trotzdem publizieren, sonst bliebe ein MQTT-Retained-Wert
    # von vor einem Neustart für immer stehen.
    broker = ConsumerValueStoreBroker(1)

    # execution
    broker.zero_power_on_sustained_error()

    # evaluation
    assert broker.state.power == 0


@pytest.mark.parametrize("tag", ["0012345678", None])
@pytest.mark.parametrize("timestamp", [1000.5, None])
def test_consumer_store_forwards_rfid_without_clearing_pending_input(tag, timestamp, mock_pub):
    store = _consumer.ConsumerValueStoreBroker(1)
    store.set(ConsumerState(rfid=tag, rfid_timestamp=timestamp))

    store.update()

    for key, value in [("rfid", tag), ("rfid_timestamp", timestamp)]:
        topic = f"openWB/set/consumer/1/get/{key}"
        calls = [call.args for call in mock_pub.pub.call_args_list if call.args[0] == topic]
        assert calls == ([(topic, value)] if value is not None else [])
