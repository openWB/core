from control.error_state import effective_power, error_duration_exceeded
from helpermodules import timecheck
from helpermodules.constants import COMPONENT_ERROR_DURATION
from modules.common.fault_state_level import FaultStateLevel


def test_effective_power_no_error_resets_timer():
    result = effective_power(1000, FaultStateLevel.NO_ERROR, 123.0)

    assert result.power == 1000
    assert result.error_timer is None
    assert result.just_expired is False


def test_effective_power_first_error_starts_timer():
    result = effective_power(1000, FaultStateLevel.ERROR, None)

    assert result.power == 1000
    assert result.error_timer is not None
    assert result.just_expired is False


def test_effective_power_within_grace_period_keeps_power(monkeypatch):
    now = timecheck.create_timestamp()
    result = effective_power(1000, FaultStateLevel.ERROR, now - (COMPONENT_ERROR_DURATION - 1))

    assert result.power == 1000
    assert result.error_timer == now - (COMPONENT_ERROR_DURATION - 1)
    assert result.just_expired is False


def test_effective_power_expired_returns_zero_and_flags_transition():
    error_timer = timecheck.create_timestamp() - (COMPONENT_ERROR_DURATION + 1)

    result = effective_power(1000, FaultStateLevel.ERROR, error_timer)

    assert result.power == 0
    assert result.error_timer == error_timer
    assert result.just_expired is True


def test_effective_power_expired_does_not_re_flag_transition():
    error_timer = timecheck.create_timestamp() - (COMPONENT_ERROR_DURATION + 1)

    result = effective_power(0, FaultStateLevel.ERROR, error_timer)

    assert result.power == 0
    assert result.just_expired is False


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
