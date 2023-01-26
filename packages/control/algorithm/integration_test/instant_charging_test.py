from dataclasses import dataclass, field
from typing import List
from unittest.mock import Mock
import pytest

from control.algorithm import additional_current
from control.algorithm.integration_test.conftest import ParamsExpectedSetCurrent, assert_expected_current
from control.chargemode import Chargemode
from control import data
from control.algorithm.algorithm import Algorithm
from control.loadmanagement import LimitingValue
from dataclass_utils.factories import currents_list_factory


@pytest.fixture()
def all_cp_instant_charging_1p():
    for i in range(3, 6):
        control_parameter = data.data.cp_data[f"cp{i}"].data.set.charging_ev_data.data.control_parameter
        control_parameter.required_currents = [0]*3
        control_parameter.required_currents[i-3] = 16
        control_parameter.required_current = 16
        control_parameter.chargemode = Chargemode.INSTANT_CHARGING
        control_parameter.submode = Chargemode.INSTANT_CHARGING


@pytest.fixture()
def all_cp_charging_1p():
    for i in range(3, 6):
        data.data.cp_data[f"cp{i}"].data.get.currents = [0]*3
        data.data.cp_data[f"cp{i}"].data.get.currents[i-3] = 16


@pytest.fixture()
def all_cp_instant_charging_3p():
    for i in range(3, 6):
        control_parameter = data.data.cp_data[f"cp{i}"].data.set.charging_ev_data.data.control_parameter
        control_parameter.required_currents = [16]*3
        control_parameter.required_current = 16
        control_parameter.chargemode = Chargemode.INSTANT_CHARGING
        data.data.cp_data[f"cp{i}"].data.get.currents = [16]*3


@dataclass
class ParamsExpectedCounterSet:
    expected_raw_power_left: float = 0
    expected_raw_currents_left_counter0: List[float] = field(default_factory=currents_list_factory)
    expected_raw_currents_left_counter6: List[float] = field(default_factory=currents_list_factory)


def assert_counter_set(params: ParamsExpectedCounterSet):
    assert data.data.counter_data["counter0"].data.set.raw_power_left == params.expected_raw_power_left
    assert data.data.counter_data["counter0"].data.set.raw_currents_left == params.expected_raw_currents_left_counter0
    assert data.data.counter_data["counter6"].data.set.raw_currents_left == params.expected_raw_currents_left_counter6


def test_start_instant_charging(all_cp_instant_charging_1p, all_cp_not_charging, monkeypatch):
    # alle 3 im Sofortladen, keine Ladung aktiv -> dürfen nur Mindeststrom zugeteilt kriegen
    # setup
    data.data.counter_data["counter0"].data.set.raw_power_left = 21310
    data.data.counter_data["counter0"].data.set.raw_currents_left = [32, 30, 31]
    data.data.counter_data["counter6"].data.set.raw_currents_left = [16, 12, 14]
    mockget_component_name_by_id = Mock(return_value="Garage")
    monkeypatch.setattr(additional_current, "get_component_name_by_id", mockget_component_name_by_id)

    # execution
    Algorithm().calc_current()

    # evaluation
    assert data.data.cp_data["cp3"].data.set.current == 10
    assert data.data.cp_data["cp4"].data.set.current == 6
    assert data.data.cp_data["cp5"].data.set.current == 6
    assert data.data.counter_data["counter0"].data.set.raw_power_left == 16250
    assert data.data.counter_data["counter0"].data.set.raw_currents_left == [22, 24, 25]
    assert data.data.counter_data["counter6"].data.set.raw_currents_left == [16, 6, 8]


@dataclass
class ParamsLimit(ParamsExpectedSetCurrent, ParamsExpectedCounterSet):
    name: str = ""
    raw_power_left: float = 0
    raw_currents_left_counter0: List[float] = field(default_factory=currents_list_factory)
    raw_currents_left_counter6: List[float] = field(default_factory=currents_list_factory)
    expected_state_str: LimitingValue = LimitingValue.CURRENT


cases_limit = [
    ParamsLimit(name="limit by current",
                raw_power_left=21310,
                raw_currents_left_counter0=[14, 30, 31],
                raw_currents_left_counter6=[16, 12, 14],
                expected_state_str=LimitingValue.CURRENT,
                expected_current_cp3=14,
                expected_current_cp4=12,
                expected_current_cp5=14,
                expected_raw_power_left=12110,
                expected_raw_currents_left_counter0=[0, 18, 17],
                expected_raw_currents_left_counter6=[16, 0, 0]),
    ParamsLimit(name="limit by power",
                raw_power_left=5520,
                raw_currents_left_counter0=[14, 30, 31],
                raw_currents_left_counter6=[16, 12, 14],
                expected_state_str=LimitingValue.POWER,
                expected_current_cp3=10.333333333333334,
                expected_current_cp4=6.833333333333333,
                expected_current_cp5=6.833333333333333,
                expected_raw_power_left=0,
                expected_raw_currents_left_counter0=[3.666666666666666, 23.166666666666668, 24.166666666666668],
                expected_raw_currents_left_counter6=[16, 5.166666666666667, 7.166666666666667]),
    # limit by unbalanced load
]


@pytest.mark.parametrize("params", cases_limit, ids=[c.name for c in cases_limit])
def test_instant_charging_limit(params: ParamsLimit, all_cp_instant_charging_1p, all_cp_charging_1p, monkeypatch):
    # setup
    data.data.counter_data["counter0"].data.set.raw_power_left = params.raw_power_left
    data.data.counter_data["counter0"].data.set.raw_currents_left = params.raw_currents_left_counter0
    data.data.counter_data["counter6"].data.set.raw_currents_left = params.raw_currents_left_counter6
    mockget_component_name_by_id = Mock(return_value="Garage")
    monkeypatch.setattr(additional_current, "get_component_name_by_id", mockget_component_name_by_id)
    # execution
    Algorithm().calc_current()

    # evaluation
    assert_expected_current(params)
    for i in range(3, 6):
        assert data.data.cp_data[
            f"cp{i}"].data.get.state_str == (f"Es kann nicht mit der vorgegebenen Stromstärke geladen werden"
                                             f"{params.expected_state_str.value.format('Garage')}")
    assert_counter_set(params)


@dataclass
class ParamsControlParameter(ParamsExpectedSetCurrent, ParamsExpectedCounterSet):
    name: str = ""
    prio_cp3: bool = False
    submode_cp3: Chargemode = Chargemode.INSTANT_CHARGING
    prio_cp4: bool = False
    submode_cp4: Chargemode = Chargemode.INSTANT_CHARGING
    prio_cp5: bool = False
    submode_cp5: Chargemode = Chargemode.INSTANT_CHARGING


cases_control_parameter = [
    ParamsControlParameter(name="lift prio cp3",
                           prio_cp3=True,
                           prio_cp4=False,
                           prio_cp5=False,
                           expected_current_cp3=16,
                           expected_current_cp4=8,
                           expected_current_cp5=8,
                           expected_raw_power_left=0,
                           expected_raw_currents_left_counter0=[0]*3,
                           expected_raw_currents_left_counter6=[0]*3),
    ParamsControlParameter(name="drop prio cp4",
                           prio_cp3=True,
                           prio_cp4=False,
                           prio_cp5=True,
                           expected_current_cp3=15,
                           expected_current_cp4=6,
                           expected_current_cp5=10,
                           expected_raw_power_left=690,
                           expected_raw_currents_left_counter0=[1]*3,
                           expected_raw_currents_left_counter6=[0]*3),
    ParamsControlParameter(name="lift submode cp4",
                           submode_cp4=Chargemode.TIME_CHARGING,
                           expected_current_cp3=13,
                           expected_current_cp4=10,
                           expected_current_cp5=6,
                           expected_raw_power_left=2070,
                           expected_raw_currents_left_counter0=[3]*3,
                           expected_raw_currents_left_counter6=[0]*3),
    # ParamsControlParameter(name="drop submode cp4",
    # niedrigster instant modus erreicht
    #                        submode_cp4=Chargemode.PV_CHARGING,
    #                        expected_current_cp3=16,
    #                        expected_current_cp4=6,
    #                        expected_current_cp5=10,
    #                        expected_raw_power_left=0,
    #                        expected_raw_currents_left_counter0=[0]*3,
    #                        expected_raw_currents_left_counter6=[0]*3)
]


@pytest.mark.parametrize("params", cases_control_parameter, ids=[c.name for c in cases_control_parameter])
def test_control_parameter_instant_charging(params: ParamsControlParameter, all_cp_instant_charging_3p, monkeypatch):
    # setup
    data.data.cp_data["cp3"].data.set.charging_ev_data.data.control_parameter.prio = params.prio_cp3
    data.data.cp_data["cp3"].data.set.charging_ev_data.data.control_parameter.submode = params.submode_cp3
    data.data.cp_data["cp4"].data.set.charging_ev_data.data.control_parameter.prio = params.prio_cp4
    data.data.cp_data["cp4"].data.set.charging_ev_data.data.control_parameter.submode = params.submode_cp4
    data.data.cp_data["cp5"].data.set.charging_ev_data.data.control_parameter.prio = params.prio_cp5
    data.data.cp_data["cp5"].data.set.charging_ev_data.data.control_parameter.submode = params.submode_cp5
    data.data.counter_data["counter0"].data.set.raw_power_left = 22080
    data.data.counter_data["counter0"].data.set.raw_currents_left = [32]*3
    data.data.counter_data["counter6"].data.set.raw_currents_left = [16]*3
    mockget_component_name_by_id = Mock(return_value="Garage")
    monkeypatch.setattr(additional_current, "get_component_name_by_id", mockget_component_name_by_id)

    # execution
    Algorithm().calc_current()

    # evaluation
    assert_expected_current(params)
    assert_counter_set(params)
