from types import SimpleNamespace

import pytest

from modules.common.component_state import ConsumerState
from modules.common.store import _consumer


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
