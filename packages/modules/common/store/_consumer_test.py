from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from control import data
from helpermodules import timecheck
from modules.common.abstract_device import AbstractDevice
from modules.common.component_state import ConsumerState, CounterState
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import _consumer
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


def _set_consumer(monkeypatch, connected_phases, extra_meter=None):
    consumer = SimpleNamespace(data=SimpleNamespace(
        config=SimpleNamespace(connected_phases=connected_phases), extra_meter=extra_meter))
    monkeypatch.setattr(_consumer.data, "data", SimpleNamespace(consumer_data={"consumer1": consumer}),
                        raising=False)


@pytest.mark.parametrize("connected_phases, expected_voltages, expected_powers, expected_currents", [
    pytest.param(1, [230, 0, 0], [230, 0, 0], [1, 0, 0], id="1 Phase"),
    pytest.param(2, [230, 230, 0], [115, 115, 0], [0.5, 0.5, 0], id="2 Phasen"),
    pytest.param(3, [230]*3, [230/3]*3, [1/3]*3, id="3 Phasen"),
])
def test_consumer_store_distributes_total_power_on_connected_phases(
        connected_phases, expected_voltages, expected_powers, expected_currents, monkeypatch):
    _set_consumer(monkeypatch, connected_phases)
    store = _consumer.ConsumerValueStoreBroker(1)

    store.set(ConsumerState(power=230))

    assert store.state.voltages == pytest.approx(expected_voltages)
    assert store.state.powers == pytest.approx(expected_powers)
    assert store.state.currents == pytest.approx(expected_currents)


def test_consumer_store_keeps_values_of_extra_meter(monkeypatch):
    _set_consumer(monkeypatch, 1, extra_meter=object())
    store = _consumer.ConsumerValueStoreBroker(1)

    store.set(ConsumerState(power=230))

    assert store.state.voltages == [230.0]*3
    assert store.state.powers == [0.0]*3


def test_consumer_store_keeps_values_of_unknown_consumer(monkeypatch):
    monkeypatch.setattr(_consumer.data, "data", SimpleNamespace(consumer_data={}), raising=False)
    store = _consumer.ConsumerValueStoreBroker(1)

    store.set(ConsumerState(power=230))

    assert store.state.voltages == [230.0]*3


def test_consumer_state_keeps_values_reported_by_the_module():
    state = ConsumerState(power=460, voltages=[230, 231, 0], currents=[0, 2, 0], powers=[0, 460, 0])

    state.distribute_total_power(1)

    assert state.voltages == [230, 231, 0]
    assert state.powers == [0, 460, 0]
    assert state.currents == [0, 2, 0]
