import pytest

from control import data, loadmanagement
from control.algorithm.additional_current import AdditionalCurrent
from control.algorithm.surplus_controlled import SurplusControlled
from control.chargemode import Chargemode
from control.chargepoint.chargepoint_state import ChargepointState


@pytest.mark.parametrize("phases", [1, 2, 3])
@pytest.mark.parametrize("consider_less_charging", [False, True])
def test_surplus_preserves_previous_allocation_across_counter_levels(phases, consider_less_charging, monkeypatch):
    """Previously allocated current must not consume surplus again at each counter."""
    monkeypatch.setattr(loadmanagement, "get_component_name_by_id", lambda num: f"counter{num}")
    data.data.counter_all_data.data.config.consider_less_charging = consider_less_charging
    for counter in data.data.counter_data.values():
        counter.data.set.raw_currents_left = [100]*3
        counter.data.set.surplus_power_left = 4000

    allocated = data.data.cp_data["cp4"]
    pv = data.data.cp_data["cp5"]
    for cp, target, required, used_phases in [(allocated, 16, 16, 3), (pv, 6, 32, phases)]:
        cp.data.control_parameter.chargemode = Chargemode.PV_CHARGING
        cp.data.control_parameter.submode = Chargemode.PV_CHARGING
        cp.data.control_parameter.state = ChargepointState.CHARGING_ALLOWED
        cp.data.control_parameter.min_current = 6
        cp.data.control_parameter.required_current = required
        cp.data.control_parameter.required_currents = [required]*used_phases + [0]*(3-used_phases)
        cp.data.control_parameter.timestamp_charge_start = 0
        cp.data.get.charge_state = True
        cp.data.get.currents = [target]*used_phases + [0]*(3-used_phases)
        cp.data.get.voltages = [230]*3
        cp.data.get.evse_current = None
        cp.data.set.target_current = target
        cp.data.set.current_prev = target
        cp.data.set.charging_ev_data.ev_template.data.nominal_difference = 0
        cp.chargemode_changed = False

    SurplusControlled().set_surplus_current([allocated, pv])

    assert allocated.data.set.current == 16
    assert pv.data.set.current == 11
    expected_surplus = 4000 - 5*phases*230 if consider_less_charging else 4000
    for counter in data.data.counter_data.values():
        assert counter.data.set.surplus_power_left == pytest.approx(expected_surplus)


@pytest.mark.parametrize("phases", [1, 2, 3])
def test_additional_current_preserves_target_across_counter_levels(phases):
    """The previous stage's allocation may differ from the configured minimum."""
    cp = data.data.cp_data["cp4"]
    cp.data.control_parameter.chargemode = Chargemode.INSTANT_CHARGING
    cp.data.control_parameter.submode = Chargemode.INSTANT_CHARGING
    cp.data.control_parameter.min_current = 6
    cp.data.control_parameter.required_current = 16
    cp.data.control_parameter.required_currents = [16]*phases + [0]*(3-phases)
    cp.data.get.charge_state = True
    cp.data.get.voltages = [230]*3
    cp.data.set.target_current = 10
    for counter in data.data.counter_data.values():
        counter.data.set.raw_currents_left = [100]*3
        counter.data.set.raw_power_left = 40000

    AdditionalCurrent().set_additional_current([cp])

    assert cp.data.set.current == 16
    for counter in data.data.counter_data.values():
        assert counter.data.set.raw_power_left == pytest.approx(40000 - 6*phases*230)
        assert counter.data.set.raw_currents_left == [94]*phases + [100]*(3-phases)
