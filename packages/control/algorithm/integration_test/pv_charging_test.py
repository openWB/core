from dataclasses import dataclass, field
from typing import List, Optional
from unittest.mock import Mock
import pytest

from control.algorithm import additional_current, surplus_controlled
from control.algorithm.integration_test.conftest import ParamsExpectedSetCurrent, assert_expected_current
from control.chargemode import Chargemode
from control import data
from control.algorithm.algorithm import Algorithm
from control.algorithm.algorithm import data as algorithm_data
from control.chargepoint.chargepoint_template import CpTemplate
from control.chargepoint.chargepoint_state import ChargepointState
from dataclass_utils.factories import currents_list_factory


@pytest.fixture()
def all_cp_pv_charging_3p():
    for i in range(3, 6):
        control_parameter = data.data.cp_data[f"cp{i}"].data.control_parameter
        control_parameter.required_current = data.data.cp_data[
            f"cp{i}"].data.set.charging_ev_data.ev_template.data.min_current
        control_parameter.required_currents = [
            data.data.cp_data[f"cp{i}"].data.set.charging_ev_data.ev_template.data.min_current]*3
        control_parameter.min_current = data.data.cp_data[
            f"cp{i}"].data.set.charging_ev_data.ev_template.data.min_current
        control_parameter.chargemode = Chargemode.PV_CHARGING
        control_parameter.submode = Chargemode.PV_CHARGING
        control_parameter.phases = 3


@pytest.fixture()
def all_cp_charging_3p():
    data.data.cp_data["cp3"].data.get.currents = [10]*3
    data.data.cp_data["cp4"].data.get.currents = [8]*3
    data.data.cp_data["cp5"].data.get.currents = [8]*3
    data.data.cp_data["cp3"].data.get.power = 6900
    data.data.cp_data["cp4"].data.get.power = 5520
    data.data.cp_data["cp5"].data.get.power = 5520

    for i in range(3, 6):
        charging_ev_data = data.data.cp_data[f"cp{i}"].data.set.charging_ev_data
        data.data.cp_data[f"cp{i}"].data.get.charge_state = True
        data.data.cp_data[f"cp{i}"].data.set.current = charging_ev_data.ev_template.data.min_current
        data.data.cp_data[f"cp{i}"].data.set.required_power = sum(
            data.data.cp_data[f"cp{i}"].data.control_parameter.required_currents) * 230
        data.data.cp_data[f"cp{i}"].data.config.auto_phase_switch_hw = True
        data.data.cp_data[f"cp{i}"].template = CpTemplate()
        data.data.cp_data[f"cp{i}"].data.control_parameter.state = ChargepointState.CHARGING_ALLOWED


@pytest.fixture()
def all_cp_pv_charging_1p():
    for i in range(3, 6):
        control_parameter = data.data.cp_data[f"cp{i}"].data.control_parameter
        charging_ev_data = data.data.cp_data[f"cp{i}"].data.set.charging_ev_data
        control_parameter.min_current = data.data.cp_data[
            f"cp{i}"].data.set.charging_ev_data.ev_template.data.min_current
        control_parameter.required_current = data.data.cp_data[
            f"cp{i}"].data.set.charging_ev_data.ev_template.data.min_current
        control_parameter.required_currents = [0]*3
        control_parameter.required_currents[i-3] = charging_ev_data.ev_template.data.min_current
        control_parameter.chargemode = Chargemode.PV_CHARGING
        control_parameter.submode = Chargemode.PV_CHARGING
        control_parameter.phases = 1
        control_parameter.state = ChargepointState.CHARGING_ALLOWED
        data.data.cp_data[f"cp{i}"].data.get.charge_state = True
        data.data.cp_data[f"cp{i}"].data.set.current = charging_ev_data.ev_template.data.min_current
        data.data.cp_data[f"cp{i}"].data.set.required_power = sum(
            data.data.cp_data[f"cp{i}"].data.control_parameter.required_currents) * 230
        data.data.cp_data[f"cp{i}"].data.config.auto_phase_switch_hw = True
        data.data.cp_data[f"cp{i}"].template = CpTemplate()
    data.data.cp_data["cp3"].data.get.currents = [16, 0, 0]
    data.data.cp_data["cp4"].data.get.currents = [8, 0, 0]
    data.data.cp_data["cp5"].data.get.currents = [8, 0, 0]
    data.data.cp_data["cp3"].data.get.power = 6900
    data.data.cp_data["cp4"].data.get.power = 5520
    data.data.cp_data["cp5"].data.get.power = 5520


@dataclass
class ParamsExpectedCounterSet:
    expected_raw_power_left: float = 0
    expected_surplus_power_left: float = 0
    expected_reserved_surplus: float = 0
    expected_released_surplus: float = 0


@dataclass
class ParamsSurplus(ParamsExpectedSetCurrent, ParamsExpectedCounterSet):
    name: str = ""
    power: float = 0
    raw_power_left: float = 0
    raw_currents_left_counter0: List[float] = field(default_factory=currents_list_factory)
    raw_currents_left_counter6: List[float] = field(default_factory=currents_list_factory)


@dataclass
class ParamsPhaseSwitch(ParamsExpectedSetCurrent, ParamsExpectedCounterSet):
    name: str = ""
    raw_power_left: float = 0
    raw_currents_left_counter0: List[float] = field(default_factory=currents_list_factory)
    raw_currents_left_counter6: List[float] = field(default_factory=currents_list_factory)
    expected_timestamp_last_phase_switch_cp3: Optional[str] = None
    expected_timestamp_last_phase_switch_cp4: Optional[str] = None
    expected_timestamp_last_phase_switch_cp5: Optional[str] = None


def assert_counter_set(params: ParamsExpectedCounterSet):
    counter0 = data.data.counter_data["counter0"]
    assert counter0.data.set.raw_power_left == params.expected_raw_power_left
    assert counter0.data.set.surplus_power_left == params.expected_surplus_power_left
    assert counter0.data.set.reserved_surplus == params.expected_reserved_surplus
    assert counter0.data.set.released_surplus == params.expected_released_surplus


def test_start_pv_delay(all_cp_pv_charging_3p, all_cp_not_charging, monkeypatch):
    # alle 3 im PV-laden, keine Ladung -> bei zwei die Verzögerung starten, für den 3. reicht es nicht
    # setup
    data.data.counter_data["counter0"].data.set.raw_power_left = 31775
    data.data.counter_data["counter0"].data.set.raw_currents_left = [32, 30, 31]
    data.data.counter_data["counter6"].data.set.raw_currents_left = [16, 12, 14]
    data.data.counter_data["counter0"].data.set.reserved_surplus = 0
    mockget_component_name_by_id = Mock(return_value="Garage")
    monkeypatch.setattr(additional_current, "get_component_name_by_id", mockget_component_name_by_id)

    # execution
    Algorithm().calc_current()

    # evaluation
    for i in range(3, 6):
        assert data.data.cp_data[f"cp{i}"].data.set.current == 0
    assert data.data.cp_data[
        "cp3"].data.control_parameter.timestamp_switch_on_off == 1652683252.0
    assert data.data.cp_data[
        "cp4"].data.control_parameter.timestamp_switch_on_off == 1652683252.0
    assert data.data.cp_data[
        "cp5"].data.control_parameter.timestamp_switch_on_off is None
    assert data.data.counter_data["counter0"].data.set.raw_power_left == 31775
    assert data.data.counter_data["counter0"].data.set.surplus_power_left == 9890
    assert data.data.counter_data["counter0"].data.set.reserved_surplus == 9000


def test_pv_delay_expired(all_cp_pv_charging_3p, all_cp_not_charging, monkeypatch):
    # alle 3 im PV-laden, keine Ladung -> bei einem die Verzögerung abgelaufen, erhält Mindeststrom
    # setup
    data.data.counter_data["counter0"].data.set.raw_power_left = 31200
    data.data.counter_data["counter0"].data.set.raw_currents_left = [32, 30, 31]
    data.data.counter_data["counter6"].data.set.raw_currents_left = [16, 12, 14]
    data.data.counter_data["counter0"].data.set.reserved_surplus = 9000
    data.data.cp_data[
        "cp3"].data.control_parameter.timestamp_switch_on_off = 1652683185.0
    data.data.cp_data[
        "cp3"].data.control_parameter.state = ChargepointState.SWITCH_ON_DELAY
    # nicht genug Überschuss für beide
    data.data.cp_data[
        "cp4"].data.control_parameter.timestamp_switch_on_off = 1652683252.0
    data.data.cp_data[
        "cp4"].data.control_parameter.state = ChargepointState.SWITCH_ON_DELAY
    data.data.cp_data[
        "cp5"].data.control_parameter.timestamp_switch_on_off = None
    mockget_component_name_by_id = Mock(return_value="Garage")
    monkeypatch.setattr(additional_current, "get_component_name_by_id", mockget_component_name_by_id)

    # execution
    Algorithm().calc_current()

    # evaluation
    assert data.data.cp_data["cp3"].data.set.current == 10
    assert data.data.cp_data["cp4"].data.set.current == 0
    assert data.data.cp_data["cp5"].data.set.current == 0
    assert data.data.cp_data[
        "cp3"].data.control_parameter.timestamp_switch_on_off is None
    assert data.data.cp_data[
        "cp4"].data.control_parameter.timestamp_switch_on_off is None
    assert data.data.cp_data[
        "cp5"].data.control_parameter.timestamp_switch_on_off is None
    assert data.data.counter_data["counter0"].data.set.raw_power_left == 24300
    assert data.data.counter_data["counter0"].data.set.surplus_power_left == 2415
    assert data.data.counter_data["counter0"].data.set.reserved_surplus == 0


cases_limit = [
    ParamsSurplus(name="surplus left",
                  power=-1090,
                  raw_power_left=50000,
                  raw_currents_left_counter0=[40]*3,
                  raw_currents_left_counter6=[16]*3,
                  expected_current_cp3=16,
                  expected_current_cp4=8,
                  expected_current_cp5=8,
                  expected_raw_power_left=34820,
                  expected_surplus_power_left=6035.0,
                  expected_reserved_surplus=0,
                  expected_released_surplus=0),
    ParamsSurplus(name="reduce current",
                  power=-1090,
                  raw_power_left=39650,
                  raw_currents_left_counter0=[40]*3,
                  raw_currents_left_counter6=[16]*3,
                  expected_current_cp3=16,
                  expected_current_cp4=7.8731884057971016,
                  expected_current_cp5=7.8731884057971016,
                  expected_raw_power_left=24470,
                  expected_surplus_power_left=0,
                  expected_reserved_surplus=0,
                  expected_released_surplus=0),
    ParamsSurplus(name="switch off delay for two of three charging",
                  power=8200,
                  raw_power_left=20815,
                  raw_currents_left_counter0=[40]*3,
                  raw_currents_left_counter6=[16]*3,
                  expected_current_cp3=10,
                  expected_current_cp4=6,
                  expected_current_cp5=6,
                  expected_raw_power_left=5635,
                  expected_surplus_power_left=-16250.0,
                  expected_reserved_surplus=0,
                  expected_released_surplus=11040),
]


@pytest.mark.parametrize("params", cases_limit, ids=[c.name for c in cases_limit])
def test_surplus(params: ParamsSurplus, all_cp_pv_charging_3p, all_cp_charging_3p, monkeypatch):
    # setup
    data.data.counter_data["counter0"].data.get.power = params.power
    data.data.counter_data["counter0"].data.set.raw_power_left = params.raw_power_left
    data.data.counter_data["counter0"].data.set.raw_currents_left = params.raw_currents_left_counter0
    data.data.counter_data["counter6"].data.set.raw_currents_left = params.raw_currents_left_counter6
    mockget_component_name_by_id = Mock(return_value="Garage")
    monkeypatch.setattr(surplus_controlled, "get_component_name_by_id", mockget_component_name_by_id)

    # execution
    Algorithm().calc_current()

    # evaluation
    assert_expected_current(params)
    assert_counter_set(params)


cases_phase_switch = [
    ParamsPhaseSwitch(name="phase switch 3p->1p",
                      raw_power_left=32580,
                      raw_currents_left_counter0=[40]*3,
                      raw_currents_left_counter6=[16]*3,
                      expected_timestamp_last_phase_switch_cp3=1652683252.0,
                      expected_timestamp_last_phase_switch_cp4=None,
                      expected_timestamp_last_phase_switch_cp5=None,
                      expected_current_cp3=10,
                      expected_current_cp4=6,
                      expected_current_cp5=6,
                      expected_raw_power_left=17400,
                      expected_surplus_power_left=-4485,
                      expected_reserved_surplus=0,
                      expected_released_surplus=0),
    ParamsPhaseSwitch(name="phase switch 1p->3p",
                      raw_power_left=42580,
                      raw_currents_left_counter0=[40]*3,
                      raw_currents_left_counter6=[16]*3,
                      expected_timestamp_last_phase_switch_cp3=1652683252.0,
                      expected_timestamp_last_phase_switch_cp4=None,
                      expected_timestamp_last_phase_switch_cp5=None,
                      expected_current_cp3=32,
                      expected_current_cp4=6,
                      expected_current_cp5=6,
                      expected_raw_power_left=37520.0,
                      expected_surplus_power_left=10575.0,
                      expected_reserved_surplus=0,
                      expected_released_surplus=0)
]


def test_phase_switch(all_cp_pv_charging_3p, all_cp_charging_3p, monkeypatch):
    # setup
    data.data.counter_data["counter0"].data.set.raw_power_left = cases_phase_switch[0].raw_power_left
    data.data.counter_data["counter0"].data.set.raw_currents_left = cases_phase_switch[0].raw_currents_left_counter0
    data.data.counter_data["counter6"].data.set.raw_currents_left = cases_phase_switch[0].raw_currents_left_counter6
    mockget_component_name_by_id = Mock(return_value="Garage")
    monkeypatch.setattr(surplus_controlled, "get_component_name_by_id", mockget_component_name_by_id)
    mockget_get_phases_chargemode = Mock(return_value=0)
    monkeypatch.setattr(algorithm_data.data.general_data, "get_phases_chargemode", mockget_get_phases_chargemode)
    data.data.cp_data[
        "cp3"].data.control_parameter.state = ChargepointState.CHARGING_ALLOWED
    data.data.cp_data[
        "cp3"].data.control_parameter.timestamp_last_phase_switch = 1652682252

    # execution
    Algorithm().calc_current()

    # evaluation
    assert_expected_current(cases_phase_switch[0])
    assert data.data.cp_data[
        "cp3"].data.control_parameter.state == ChargepointState.PHASE_SWITCH_DELAY
    assert_counter_set(cases_phase_switch[0])


def test_phase_switch_1p_3p(all_cp_pv_charging_1p, monkeypatch):
    # setup
    data.data.counter_data["counter0"].data.get.power = -3000
    data.data.counter_data["counter0"].data.set.raw_power_left = cases_phase_switch[1].raw_power_left
    data.data.counter_data["counter0"].data.set.raw_currents_left = cases_phase_switch[1].raw_currents_left_counter0
    data.data.counter_data["counter6"].data.set.raw_currents_left = cases_phase_switch[1].raw_currents_left_counter6
    mockget_component_name_by_id = Mock(return_value="Garage")
    monkeypatch.setattr(surplus_controlled, "get_component_name_by_id", mockget_component_name_by_id)
    mockget_get_phases_chargemode = Mock(return_value=0)
    monkeypatch.setattr(algorithm_data.data.general_data, "get_phases_chargemode", mockget_get_phases_chargemode)
    data.data.cp_data["cp3"].data.get.currents = [32, 0, 0]
    data.data.cp_data["cp3"].data.get.power = 7360
    data.data.cp_data["cp3"].data.control_parameter.timestamp_last_phase_switch = 1652682252
    data.data.cp_data["cp4"].data.get.currents = [0, 0, 0]
    data.data.cp_data["cp5"].data.get.currents = [0, 0, 0]

    # execution
    Algorithm().calc_current()

    # evaluation
    assert_counter_set(cases_phase_switch[1])
    assert data.data.cp_data[
        "cp3"].data.control_parameter.state == ChargepointState.PHASE_SWITCH_DELAY
