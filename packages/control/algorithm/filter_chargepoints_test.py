from dataclasses import dataclass
from typing import List
from unittest.mock import Mock

import pytest

from control import data
from control.algorithm import filter_chargepoints
from control.chargemode import Chargemode
from control.chargepoint.chargepoint import Chargepoint, ChargepointData
from control.chargepoint.chargepoint_data import Log, Set
from control.chargepoint.control_parameter import ControlParameter
from control.counter_all import CounterAll
from control.ev.ev import Ev, EvData, Get


@pytest.fixture()
def mock_data() -> None:
    data.data_init(Mock())


@dataclass
class PreferencedParams:
    name: str
    expected_sort: List
    plug_time_1: str = "10/31/2022, 07:00:00"
    imported_since_plugged_1: float = 100
    soc_1: float = 50
    required_current_1: float = 6
    plug_time_2: str = "10/31/2022, 07:00:00"
    imported_since_plugged_2: float = 100
    soc_2: float = 50
    required_current_2: float = 6
    plug_time_3: str = "10/31/2022, 07:00:00"
    imported_since_plugged_3: float = 100
    soc_3: float = 50
    required_current_3: float = 6


@pytest.fixture(autouse=True)
def mock_cp1() -> Chargepoint:
    return Chargepoint(1, None)


@pytest.fixture(autouse=True)
def mock_cp2() -> Chargepoint:
    return Chargepoint(2, None)


@pytest.fixture(autouse=True)
def mock_cp3() -> Chargepoint:
    return Chargepoint(3, None)


preferenced_cases = [
    PreferencedParams("sort by num", [mock_cp1, mock_cp2, mock_cp3]),
    PreferencedParams("sort by imported_since_plugged", [
                      mock_cp2, mock_cp3, mock_cp1], imported_since_plugged_2=20, imported_since_plugged_3=60),
    PreferencedParams("sort by plug_time", [mock_cp2, mock_cp1, mock_cp3],
                      plug_time_2="10/31/2022, 06:00:00", plug_time_3="10/31/2022, 12:00:00"),
    PreferencedParams("sort by soc", [mock_cp2, mock_cp1, mock_cp3], soc_2=20, soc_3=60),
    PreferencedParams("sort by required_current", [mock_cp1, mock_cp2,
                      mock_cp3], required_current_2=7, required_current_3=8),
    PreferencedParams("sort by required_current and soc", [
                      mock_cp2, mock_cp1, mock_cp3], required_current_2=7, soc_2=40),
]


@pytest.mark.parametrize("params", preferenced_cases, ids=[c.name for c in preferenced_cases])
def test_get_preferenced_chargepoint(params: PreferencedParams):
    # setup
    def mock_cp(cp: Chargepoint, num: int):
        ev = Ev(0)
        ev.data = EvData(get=Get(soc=getattr(params, f"soc_{num}")))
        cp.data = ChargepointData(set=Set(plug_time=getattr(params, f"plug_time_{num}"), log=Log(
            imported_since_plugged=getattr(params, f"imported_since_plugged_{num}")), charging_ev_data=ev),
            control_parameter=ControlParameter(
            required_current=getattr(params, f"required_current_{num}")))
        cp.num = num
        return cp

    cp1 = mock_cp(mock_cp1, 1)
    cp2 = mock_cp(mock_cp2, 2)
    cp3 = mock_cp(mock_cp3, 3)
    # execution
    preferenced_chargepoints = filter_chargepoints._get_preferenced_chargepoint([cp1, cp2, cp3])

    # evaluation
    assert preferenced_chargepoints == params.expected_sort


preferenced_cases = [
    PreferencedParams("sort by num", [mock_cp1, mock_cp2, mock_cp3]),

    PreferencedParams("sort by soc", [mock_cp2, mock_cp1, mock_cp3], soc_2=20, soc_3=60),
    PreferencedParams("sort by required_current", [mock_cp1, mock_cp2,
                      mock_cp3], required_current_2=7, required_current_3=8),
    PreferencedParams("sort by required_current and soc", [
                      mock_cp2, mock_cp1, mock_cp3], required_current_2=7, soc_2=40),
]


@pytest.mark.parametrize(
    "required_current_1, expected_cp_indices",
    [
        pytest.param(6, [1, 2], id="fits mode"),
        pytest.param(0, [2], id="cp1 should not charge"),
    ])
def test_get_chargepoints_by_mode(required_current_1: int,
                                  expected_cp_indices,
                                  mock_cp1, mock_cp2):
    # setup
    def setup_cp(cp: Chargepoint, required_current: float) -> Chargepoint:
        cp.data.set.charging_ev_data = Ev(cp.num)
        cp.data.config.ev = cp.num
        cp.data.control_parameter.required_current = required_current
        cp.data.control_parameter.chargemode = Chargemode.SCHEDULED_CHARGING
        cp.data.control_parameter.submode = Chargemode.INSTANT_CHARGING
        cp.data.set.plug_time = 1
        return cp
    data.data.cp_data = {"cp1": setup_cp(mock_cp1, required_current_1),
                         "cp2": setup_cp(mock_cp2, 6)}

    # evaluation
    valid_chargepoints = filter_chargepoints.get_chargepoints_by_mode(
        ((Chargemode.SCHEDULED_CHARGING, Chargemode.INSTANT_CHARGING),))

    # assertion
    cp_mapping = {1: mock_cp1, 2: mock_cp2}
    expected_valid_chargepoints = [cp_mapping[i] for i in expected_cp_indices]
    assert valid_chargepoints == expected_valid_chargepoints


@pytest.mark.parametrize(
    "chargepoints_of_counter, chargepoints_by_mode_indices, expected_cp_indices",
    [
        pytest.param(["cp1", "cp2"], [1, 2], [1, 2], id="match all"),
        pytest.param(["cp1", "cp2"], [1], [1], id="match by mode"),
        pytest.param(["cp2"], [1, 2], [2], id="match by counter"),
        pytest.param(["cp1"], [2], [], id="match none")
    ])
def test_get_chargepoints_by_mode_and_counter(chargepoints_of_counter: List[str],
                                              chargepoints_by_mode_indices: List[int],
                                              expected_cp_indices: List[int],
                                              monkeypatch, mock_cp1, mock_cp2, mock_data):
    # setup
    cp_mapping = {1: mock_cp1, 2: mock_cp2}
    chargepoints_by_mode = [cp_mapping[i] for i in chargepoints_by_mode_indices]
    expected_chargepoints = [cp_mapping[i] for i in expected_cp_indices]

    get_chargepoints_of_counter_mock = Mock(return_value=chargepoints_of_counter)
    monkeypatch.setattr(CounterAll, "get_chargepoints_of_counter", get_chargepoints_of_counter_mock)
    get_chargepoints_by_mode_mock = Mock(return_value=chargepoints_by_mode)
    monkeypatch.setattr(filter_chargepoints, "get_chargepoints_by_mode", get_chargepoints_by_mode_mock)
    data.data.counter_all_data = CounterAll()

    # evaluation
    valid_chargepoints = filter_chargepoints.get_chargepoints_by_mode_and_counter_and_lm_prio(Mock(), "counter6", (
                                                                                              mock_cp1, mock_cp2))

    # assertion
    assert valid_chargepoints == expected_chargepoints
