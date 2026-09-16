from control.error_state import MAX_ERROR_DURATION, effective_power
from helpermodules import timecheck
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
    result = effective_power(1000, FaultStateLevel.ERROR, now - (MAX_ERROR_DURATION - 1))

    assert result.power == 1000
    assert result.error_timer == now - (MAX_ERROR_DURATION - 1)
    assert result.just_expired is False


def test_effective_power_expired_returns_zero_and_flags_transition():
    error_timer = timecheck.create_timestamp() - (MAX_ERROR_DURATION + 1)

    result = effective_power(1000, FaultStateLevel.ERROR, error_timer)

    assert result.power == 0
    assert result.error_timer == error_timer
    assert result.just_expired is True


def test_effective_power_expired_does_not_re_flag_transition():
    error_timer = timecheck.create_timestamp() - (MAX_ERROR_DURATION + 1)

    result = effective_power(0, FaultStateLevel.ERROR, error_timer)

    assert result.power == 0
    assert result.just_expired is False
