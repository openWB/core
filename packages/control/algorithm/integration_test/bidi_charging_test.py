import pytest
from unittest.mock import Mock

from control import data
from control import loadmanagement
from control.algorithm.algorithm import Algorithm
from control.chargemode import Chargemode


@pytest.fixture()
def bidi_cps():
    def _setup(*cps):
        for counter in ("counter0", "counter6"):
            data.data.counter_data[counter].data.set.raw_currents_left = [32]*3
            data.data.counter_data[counter].data.set.raw_exported_currents_left = [32]*3
            data.data.counter_data[counter].data.set.raw_power_left = 22000
            data.data.counter_data[counter].data.set.raw_exported_power_left = 22000
        for cp in cps:
            data.data.cp_data[cp].data.get.max_discharge_power = -11000
            data.data.cp_data[cp].data.get.max_charge_power = 11000
            data.data.cp_data[cp].data.get.phases_in_use = 3
            control_parameter = data.data.cp_data[cp].data.control_parameter
            control_parameter.min_current = data.data.cp_data[cp].data.set.charging_ev_data.ev_template.data.min_current
            control_parameter.phases = 3
            control_parameter.required_currents = [16]*3
            control_parameter.required_current = 16
            control_parameter.chargemode = Chargemode.SCHEDULED_CHARGING
            control_parameter.submode = Chargemode.BIDI_CHARGING
    return _setup


@pytest.mark.parametrize("grid_power, expected_current",
                         [pytest.param(-2000, 2.898550724637681, id="bidi charge"),
                          pytest.param(2000, -2.898550724637681, id="bidi discharge")])
def test_cp3_bidi(grid_power: float, expected_current: float, bidi_cps, all_cp_not_charging, monkeypatch):
    # setup
    bidi_cps("cp3")
    data.data.counter_data["counter0"].data.get.power = grid_power
    return_mock = Mock(return_value=True)
    mock_get_component_name_by_id = Mock(return_value="Garage")
    monkeypatch.setattr(loadmanagement, "get_component_name_by_id", mock_get_component_name_by_id)
    monkeypatch.setattr(
        data.data.cp_data["cp3"].data.set.charging_ev_data.charge_template, "bidi_charging_allowed", return_mock)

    # execution
    Algorithm().calc_current()

    # evaluation
    assert data.data.cp_data["cp3"].data.set.current == expected_current
    assert data.data.cp_data["cp4"].data.set.current == 0
    assert data.data.cp_data["cp5"].data.set.current == 0
    assert data.data.counter_data["counter0"].data.set.surplus_power_left == 0


def test_cp3_cp4_bidi_discharge(bidi_cps, all_cp_not_charging, monkeypatch):
    # setup
    bidi_cps("cp3", "cp4")
    data.data.counter_data["counter0"].data.get.power = 4000
    mock_get_component_name_by_id = Mock(return_value="Garage")
    monkeypatch.setattr(loadmanagement, "get_component_name_by_id", mock_get_component_name_by_id)

    # execution
    Algorithm().calc_current()

    # evaluation
    assert data.data.cp_data["cp3"].data.set.current == -2.898550724637681
    assert data.data.cp_data["cp4"].data.set.current == -2.898550724637681
    assert data.data.cp_data["cp5"].data.set.current == 0
    assert data.data.counter_data["counter0"].data.set.surplus_power_left == 0
