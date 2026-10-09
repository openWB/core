from unittest.mock import Mock

from helpermodules import timecheck
from helpermodules.constants import COMPONENT_ERROR_DURATION
from modules.common.component_context import MultiComponentUpdateContext, SingleComponentUpdateContext
from modules.common.fault_state import ComponentInfo, FaultState


def _component() -> FaultState:
    return FaultState(ComponentInfo(1, "Test", "pv"))


def test_error_timestamp_persists_across_repeated_failed_reads(monkeypatch):
    # setup - no_error() läuft vor jedem Lesen (update_always=True), darf error_timestamp dabei nicht löschen.
    fault_state = _component()
    now = timecheck.create_timestamp()
    monkeypatch.setattr(timecheck, "create_timestamp", lambda: now)

    def failing_read():
        raise Exception("Lesefehler")

    with SingleComponentUpdateContext(fault_state):
        failing_read()
    first_timestamp = fault_state.error_timestamp
    assert first_timestamp is not None

    # execution - mehrere weitere Zyklen mit demselben andauernden Fehler
    monkeypatch.setattr(timecheck, "create_timestamp", lambda: now + 30)
    for _ in range(3):
        with SingleComponentUpdateContext(fault_state):
            failing_read()

    # evaluation - Zeitstempel bleibt der allererste, wird nicht pro Zyklus neu gesetzt
    assert fault_state.error_timestamp == first_timestamp


def test_error_duration_exceeded_becomes_true_after_repeated_failed_reads(monkeypatch):
    # setup
    fault_state = _component()
    now = timecheck.create_timestamp()
    monkeypatch.setattr(timecheck, "create_timestamp", lambda: now)

    def failing_read():
        raise Exception("Lesefehler")

    with SingleComponentUpdateContext(fault_state):
        failing_read()
    assert fault_state.error_duration_exceeded() is False

    # execution - Zeit vergeht, weitere Zyklen scheitern weiterhin
    monkeypatch.setattr(timecheck, "create_timestamp", lambda: now + COMPONENT_ERROR_DURATION + 1)
    with SingleComponentUpdateContext(fault_state):
        failing_read()

    # evaluation
    assert fault_state.error_duration_exceeded() is True


def test_error_timestamp_persists_with_nested_single_component_context(monkeypatch):
    # setup - Pattern wie bei Kostal Plenticore/Fronius/RCT: MultiComponentUpdateContext mit innerem
    # SingleComponentUpdateContext pro Komponente.
    fault_state = _component()
    component = type("Component", (), {"fault_state": fault_state})()
    now = timecheck.create_timestamp()
    monkeypatch.setattr(timecheck, "create_timestamp", lambda: now)

    def failing_read():
        raise Exception("Lesefehler")

    with MultiComponentUpdateContext([component]):
        with SingleComponentUpdateContext(component.fault_state):
            failing_read()
    first_timestamp = fault_state.error_timestamp
    assert first_timestamp is not None

    # execution - mehrere weitere Zyklen
    monkeypatch.setattr(timecheck, "create_timestamp", lambda: now + 30)
    for _ in range(3):
        with MultiComponentUpdateContext([component]):
            with SingleComponentUpdateContext(component.fault_state):
                failing_read()

    # evaluation
    assert fault_state.error_timestamp == first_timestamp


def test_error_timestamp_clears_after_successful_read(monkeypatch):
    # setup
    fault_state = _component()
    now = timecheck.create_timestamp()
    monkeypatch.setattr(timecheck, "create_timestamp", lambda: now)

    def failing_read():
        raise Exception("Lesefehler")

    with SingleComponentUpdateContext(fault_state):
        failing_read()
    assert fault_state.error_timestamp is not None

    # execution - Lesen klappt wieder
    with SingleComponentUpdateContext(fault_state):
        pass

    # evaluation
    assert fault_state.error_timestamp is None
    assert fault_state.error_duration_exceeded() is False


def test_on_sustained_error_fires_from_read_phase_once_duration_exceeded(monkeypatch):
    # setup - zentraler Regressionstest: on_sustained_error feuert aus dem Lese-Zyklus, unabhängig von
    # update_values()/loadvars.py.
    fault_state = _component()
    on_sustained_error = Mock()
    fault_state.on_sustained_error = on_sustained_error
    now = timecheck.create_timestamp()
    monkeypatch.setattr(timecheck, "create_timestamp", lambda: now)

    def failing_read():
        raise Exception("Lesefehler")

    with SingleComponentUpdateContext(fault_state):
        failing_read()
    on_sustained_error.assert_not_called()

    # execution
    monkeypatch.setattr(timecheck, "create_timestamp", lambda: now + COMPONENT_ERROR_DURATION + 1)
    with SingleComponentUpdateContext(fault_state):
        failing_read()

    # evaluation
    on_sustained_error.assert_called_once()


def test_on_sustained_error_does_not_fire_within_grace_period(monkeypatch):
    # setup
    fault_state = _component()
    on_sustained_error = Mock()
    fault_state.on_sustained_error = on_sustained_error
    now = timecheck.create_timestamp()
    monkeypatch.setattr(timecheck, "create_timestamp", lambda: now)

    def failing_read():
        raise Exception("Lesefehler")

    with SingleComponentUpdateContext(fault_state):
        failing_read()

    # execution - noch innerhalb der Gnadenfrist
    monkeypatch.setattr(timecheck, "create_timestamp", lambda: now + (COMPONENT_ERROR_DURATION - 1))
    with SingleComponentUpdateContext(fault_state):
        failing_read()

    # evaluation
    on_sustained_error.assert_not_called()
