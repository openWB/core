import copy
from unittest.mock import Mock

import pytest

from control.ev.ev import Ev
from helpermodules import timecheck
from modules.common import store
from modules.common.abstract_vehicle import GeneralVehicleConfig, VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle, SocSource
from modules.vehicles.mqtt.config import MqttSocSetup

NOW = 1652683252  # packages/conftest.py fixes the clock to this timestamp.


def vehicle(updater=None, override=None, **kwargs):
    return ConfigurableVehicle(MqttSocSetup(), updater or Mock(return_value=CarState(soc=50)), vehicle=0,
                               request_interval_override=override, **kwargs)


@pytest.mark.parametrize("interval", [0, -1, float("inf"), float("nan")])
def test_invalid_override_is_rejected(interval):
    with pytest.raises(ValueError, match="finite and greater than zero"):
        vehicle(override=lambda: interval).get_request_interval_override()


def test_default_has_no_override():
    assert vehicle().get_request_interval_override() is None


@pytest.mark.parametrize("counter, fault_state, charging, override, expected_interval", [
    (0, 0, False, None, 600),
    (0, 0, True, None, 300),
    (0, 2, False, None, 300),
    (3, 2, False, None, 600),
    (10, 1, False, 60, 60),  # Cache warning still gets one-minute retries.
    (10, 2, False, 60, 60),  # Independent of the three-error limit.
    (0, 0, True, 60, 60),
    (0, 0, False, 1200, 600),  # Cannot postpone a regular request.
    (0, 0, True, 1200, 300),
])
def test_scheduler_applies_override_after_regular_interval_selection(
        counter, fault_state, charging, override, expected_interval, monkeypatch):
    ev = Ev(0)
    ev.soc_module = vehicle(override=lambda: override, general_config=GeneralVehicleConfig(
        request_interval_charging=300, request_interval_not_charging=600))
    ev.data.get.soc_request_timestamp = NOW - 30
    ev.data.get.fault_state = fault_state
    ev.data.set.soc_error_counter = counter
    check = Mock(return_value=True)
    monkeypatch.setattr(timecheck, "check_timestamp", check)

    assert not ev.soc_interval_expired(VehicleUpdateData(charge_state=charging))
    check.assert_called_once_with(NOW - 30, expected_interval - 5)


@pytest.mark.parametrize("elapsed, expected", [(30, False), (60, True)])
def test_retry_uses_last_real_request_time(elapsed, expected):
    ev = Ev(0)
    ev.soc_module = vehicle(override=lambda: 60)
    ev.data.get.soc_request_timestamp = NOW - elapsed
    ev.data.get.fault_state = 1
    ev.data.set.soc_error_counter = 10
    assert ev.soc_interval_expired(VehicleUpdateData()) is expected
    assert ev.data.get.soc_request_timestamp == NOW - elapsed


def test_only_plugged_policy_is_preserved():
    ev = Ev(0)
    ev.soc_module = vehicle(override=lambda: 60, general_config=GeneralVehicleConfig(request_only_plugged=True))
    ev.data.get.soc_request_timestamp = NOW - 120
    assert not ev.soc_interval_expired(VehicleUpdateData(plug_state=False))
    assert ev.soc_interval_expired(VehicleUpdateData(plug_state=True))


@pytest.mark.parametrize("override, cp_soc, expected", [
    (60, None, SocSource.API),
    (60, 50, SocSource.API),
    (None, None, SocSource.CALCULATION),
    (None, 50, SocSource.CP),
])
def test_retry_uses_api_even_when_soc_would_normally_be_calculated(override, cp_soc, expected):
    module = vehicle(override=lambda: override, calc_while_charging=True,
                     general_config=GeneralVehicleConfig(use_soc_from_cp=True))
    update = VehicleUpdateData(charge_state=True, soc_from_cp=cp_soc, timestamp_soc_from_cp=NOW)
    assert module._get_carstate_source(update) == expected


@pytest.mark.parametrize("has_cache", [False, True])
def test_module_error_state_and_cache_survive_scheduler_copies(has_cache, monkeypatch):
    last_request_failed = False
    cached_state = (CarState(soc=50, soc_timestamp=NOW - 300, warning="Portal temporarily unavailable")
                    if has_cache else None)
    portal = Mock(side_effect=[RuntimeError("Portal unavailable"), CarState(soc=60, soc_timestamp=NOW)])

    def fetch(update):
        nonlocal last_request_failed, cached_state
        try:
            cached_state = portal()
        except RuntimeError:
            last_request_failed = True
            if cached_state is None:
                raise
        else:
            last_request_failed = False
        return cached_state

    value_store = Mock()
    monkeypatch.setattr(store, "get_car_value_store", Mock(return_value=value_store))
    module = vehicle(updater=fetch, override=lambda: 60 if last_request_failed else None, calc_while_charging=True)
    copied = copy.deepcopy(module)
    if has_cache:
        state = copied._get_carstate_by_source(VehicleUpdateData(), SocSource.API)
        assert state.soc == 50
        assert state.soc_timestamp == NOW - 300
        assert state.warning == "Portal temporarily unavailable"
    else:
        with pytest.raises(Exception, match="Portal unavailable"):
            copied._get_carstate_by_source(VehicleUpdateData(), SocSource.API)
    assert module.get_request_interval_override() == 60

    # The next scheduler copy observes the failure, calls the API during charging,
    # and its success restores the normal schedule/source on the original object.
    next_copy = copy.deepcopy(module)
    next_copy.update(VehicleUpdateData(charge_state=True))
    assert portal.call_count == 2
    assert module.get_request_interval_override() is None
    assert module._get_carstate_source(VehicleUpdateData(charge_state=True)) == SocSource.CALCULATION


def test_new_module_instance_does_not_inherit_old_override():
    old_module = vehicle(override=lambda: 60)
    replacement = vehicle()
    assert old_module.get_request_interval_override() == 60
    assert replacement.get_request_interval_override() is None
