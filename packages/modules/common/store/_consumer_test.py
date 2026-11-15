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


def _published(mock_pub, topic):
    calls = [call.args[1] for call in mock_pub.pub.call_args_list if call.args[0] == topic]
    assert len(calls) == 1
    return calls[0]


def _set_consumer(monkeypatch, connected_phases, phase_1=1, extra_meter=None):
    consumer = SimpleNamespace(data=SimpleNamespace(
        config=SimpleNamespace(connected_phases=connected_phases, phase_1=phase_1), extra_meter=extra_meter))
    monkeypatch.setattr(_consumer.data, "data", SimpleNamespace(consumer_data={"consumer1": consumer}),
                        raising=False)


def _publish(state: ConsumerState, mock_pub):
    store = _consumer.ConsumerValueStoreBroker(1)
    store.set(state)
    store.update()
    return {key: _published(mock_pub, f"openWB/set/consumer/1/get/{key}")
            for key in ("voltages", "powers", "currents", "power")}


@pytest.mark.parametrize("connected_phases, phase_1, expected_voltages, expected_powers, expected_currents", [
    pytest.param(1, 1, [230, 0, 0], [1380, 0, 0], [6, 0, 0], id="1 Phase auf L1"),
    pytest.param(1, 2, [0, 230, 0], [0, 1380, 0], [0, 6, 0], id="1 Phase auf L2"),
    pytest.param(1, 3, [0, 0, 230], [0, 0, 1380], [0, 0, 6], id="1 Phase auf L3"),
    pytest.param(2, 1, [230, 230, 0], [690, 690, 0], [3, 3, 0], id="2 Phasen ab L1"),
    pytest.param(2, 2, [0, 230, 230], [0, 690, 690], [0, 3, 3], id="2 Phasen ab L2"),
    pytest.param(2, 3, [230, 0, 230], [690, 0, 690], [3, 0, 3], id="2 Phasen ab L3 (L3 und L1)"),
    pytest.param(3, 1, [230, 230, 230], [460, 460, 460], [2, 2, 2], id="3 Phasen"),
    pytest.param(3, 2, [230, 230, 230], [460, 460, 460], [2, 2, 2], id="3 Phasen, Phase 1 egal"),
])
def test_consumer_store_publishes_total_power_on_connected_phases_of_the_evu(
        connected_phases, phase_1, expected_voltages, expected_powers, expected_currents, monkeypatch, mock_pub):
    _set_consumer(monkeypatch, connected_phases, phase_1)

    published = _publish(ConsumerState(power=1380), mock_pub)

    assert published["voltages"] == pytest.approx(expected_voltages)
    assert published["powers"] == pytest.approx(expected_powers)
    assert published["currents"] == pytest.approx(expected_currents)
    assert published["power"] == 1380


def test_consumer_store_without_power_shows_voltage_only_on_the_selected_phase(monkeypatch, mock_pub):
    _set_consumer(monkeypatch, 1, phase_1=2)

    published = _publish(ConsumerState(power=0), mock_pub)

    assert published["voltages"] == [0, 230, 0]
    assert published["powers"] == [0, 0, 0]
    assert published["currents"] == [0, 0, 0]


def test_consumer_store_moves_values_reported_by_the_module_to_the_selected_phase(monkeypatch, mock_pub):
    """ Module liefern die Werte in der Reihenfolge der eigenen Phasen (Shelly zB immer ab Phase 1). """
    _set_consumer(monkeypatch, 2, phase_1=2)

    published = _publish(ConsumerState(power=3000, voltages=[231.0, 232.0, 0.0], currents=[5.0, 4.0, 0.0],
                                       powers=[1150.0, 920.0, 0.0]), mock_pub)

    assert published["voltages"] == [0.0, 231.0, 232.0]
    assert published["currents"] == [0.0, 5.0, 4.0]
    assert published["powers"] == [0.0, 1150.0, 920.0]


def test_consumer_store_keeps_values_of_separate_meter(monkeypatch, mock_pub):
    """ Ein separater Zähler liefert die Werte bereits je Phase des EVU. """
    _set_consumer(monkeypatch, 1, phase_1=2, extra_meter=7)

    published = _publish(ConsumerState(power=1380, currents=[0.0, 6.0, 0.0], voltages=[229.0, 230.0, 231.0]), mock_pub)

    assert published["voltages"] == [229.0, 230.0, 231.0]
    assert published["currents"] == [0.0, 6.0, 0.0]


def test_consumer_store_keeps_values_for_unknown_phase_1(monkeypatch, mock_pub):
    _set_consumer(monkeypatch, 1, phase_1=0)

    published = _publish(ConsumerState(power=0), mock_pub)

    assert published["voltages"] == [230, 0, 0]
    assert published["currents"] == [0, 0, 0]


def test_consumer_store_moves_complete_lists_even_if_voltages_have_unexpected_length(monkeypatch, mock_pub):
    """ Nutzerdefinierte Module können zu kurze Listen liefern, der ConsumerState verlangt nur für Strom und
    Leistung drei Werte. Das darf die Aktualisierung nicht abbrechen, vollständige Listen werden trotzdem auf die
    Phasen des EVU gelegt, damit das Lastmanagement den Strom auf der richtigen Phase abzieht. """
    _set_consumer(monkeypatch, 1, phase_1=2)
    state = ConsumerState(power=1380, currents=[6.0, 0.0, 0.0], powers=[1380.0, 0.0, 0.0], voltages=[230.0, 230.0])

    published = _publish(state, mock_pub)

    assert published["voltages"] == [230.0, 230.0]
    assert published["currents"] == [0.0, 6.0, 0.0]
    assert published["powers"] == [0.0, 1380.0, 0.0]


def test_consumer_store_does_not_change_the_state_of_the_module(monkeypatch, mock_pub):
    """ Der veröffentlichte Zustand ist eine Kopie, andere Threads sehen nie einen halb umgerechneten Zustand. """
    _set_consumer(monkeypatch, 1, phase_1=2)
    state = ConsumerState(power=1380)
    store = _consumer.ConsumerValueStoreBroker(1)

    store.set(state)

    assert state.voltages == [230.0, 230.0, 230.0]
    assert state.currents == [0.0, 0.0, 0.0]
    assert store.state is not state
    assert store.state.voltages == [0.0, 230.0, 0.0]


def test_consumer_store_without_known_consumer_keeps_values(mock_pub):
    published = _publish(ConsumerState(power=1380), mock_pub)

    assert published["voltages"] == [230, 230, 230]
