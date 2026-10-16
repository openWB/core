from control.error_state import error_duration_exceeded, tick_error_timer
from helpermodules import timecheck
from helpermodules.constants import COMPONENT_ERROR_DURATION
from modules.common.fault_state_level import FaultStateLevel


def test_tick_error_timer_no_error_resets_timer():
    assert tick_error_timer(FaultStateLevel.NO_ERROR, 123.0) is None


def test_tick_error_timer_first_error_starts_timer():
    assert tick_error_timer(FaultStateLevel.ERROR, None) is not None


def test_tick_error_timer_keeps_existing_timer():
    error_timer = timecheck.create_timestamp() - 30
    assert tick_error_timer(FaultStateLevel.ERROR, error_timer) == error_timer


def test_error_duration_exceeded_no_error():
    assert error_duration_exceeded(FaultStateLevel.NO_ERROR, None) is False


def test_error_duration_exceeded_error_no_timer_yet():
    assert error_duration_exceeded(FaultStateLevel.ERROR, None) is False


def test_error_duration_exceeded_within_grace_period():
    error_timer = timecheck.create_timestamp() - (COMPONENT_ERROR_DURATION - 1)
    assert error_duration_exceeded(FaultStateLevel.ERROR, error_timer) is False


def test_error_duration_exceeded_after_grace_period():
    error_timer = timecheck.create_timestamp() - (COMPONENT_ERROR_DURATION + 1)
    assert error_duration_exceeded(FaultStateLevel.ERROR, error_timer) is True
