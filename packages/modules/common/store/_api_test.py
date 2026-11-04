from unittest.mock import Mock

from helpermodules import timecheck
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.fault_state_level import FaultStateLevel
from modules.common.store._api import update_values


def _faulted_component(store):
    fault_state = FaultState(ComponentInfo(1, "Test", "counter"))
    fault_state.error("Fehler")
    fault_state.error_timestamp = timecheck.create_timestamp() - 61
    return Mock(fault_state=fault_state, store=store)


def test_update_values_still_publishes_when_store_has_no_zero_power_hook():
    # setup - zB Counter definiert absichtlich kein zero_power_on_sustained_error()
    store = Mock(spec=["set", "update"])
    component = _faulted_component(store)

    # execution
    update_values(component)

    # evaluation
    store.update.assert_called_once()


def test_update_values_zeroes_power_on_sustained_error():
    # setup
    store = Mock()
    component = _faulted_component(store)

    # execution
    update_values(component)

    # evaluation
    store.zero_power_on_sustained_error.assert_called_once()
    store.update.assert_called_once()


def test_update_values_does_not_zero_power_within_grace_period():
    # setup
    store = Mock()
    fault_state = FaultState(ComponentInfo(1, "Test", "pv"))
    fault_state.error("Fehler")
    fault_state.error_timestamp = timecheck.create_timestamp() - 30
    component = Mock(fault_state=fault_state, store=store)

    # execution
    update_values(component)

    # evaluation
    store.zero_power_on_sustained_error.assert_not_called()
    store.update.assert_called_once()


def test_update_values_does_not_zero_power_without_error():
    # setup
    store = Mock()
    fault_state = FaultState(ComponentInfo(1, "Test", "pv"))
    fault_state.fault_state = FaultStateLevel.NO_ERROR
    component = Mock(fault_state=fault_state, store=store)

    # execution
    update_values(component)

    # evaluation
    store.zero_power_on_sustained_error.assert_not_called()
    store.update.assert_called_once()
