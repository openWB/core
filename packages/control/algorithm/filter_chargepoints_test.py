from dataclasses import dataclass
from typing import List, Optional, Tuple
from unittest.mock import Mock

import pytest

from control import data
from control.algorithm import filter_chargepoints
from control.chargemode import Chargemode
from control.chargepoint import Chargepoint, ChargepointData, Log, Set
from control.counter_all import CounterAll
from control.ev import ControlParameter, Ev, EvData, Get


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
        ev.data = EvData(control_parameter=ControlParameter(
            required_current=getattr(params, f"required_current_{num}")),
            get=Get(soc=getattr(params, f"soc_{num}")))
        cp.data = ChargepointData(set=Set(plug_time=getattr(params, f"plug_time_{num}"), log=Log(
            imported_since_plugged=getattr(params, f"imported_since_plugged_{num}")), charging_ev_data=ev))
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
    "set_mode_tuple, charging_ev_1, mode_tuple_1, charging_ev_2, mode_tuple_2, expected_valid_chargepoints",
    [
        pytest.param((Chargemode.SCHEDULED_CHARGING, Chargemode.INSTANT_CHARGING, False),
                     1, (Chargemode.SCHEDULED_CHARGING,
                         Chargemode.INSTANT_CHARGING, False),
                     1, (Chargemode.SCHEDULED_CHARGING,
                         Chargemode.INSTANT_CHARGING, False),
                     [mock_cp1, mock_cp2], id="fits mode"),
        pytest.param((Chargemode.SCHEDULED_CHARGING, Chargemode.INSTANT_CHARGING, False),
                     -1, (Chargemode.SCHEDULED_CHARGING,
                          Chargemode.INSTANT_CHARGING, False),
                     1, (Chargemode.SCHEDULED_CHARGING,
                         Chargemode.INSTANT_CHARGING, False),
                     [mock_cp2], id="cp1 has no charging car"),
        pytest.param((Chargemode.SCHEDULED_CHARGING, Chargemode.INSTANT_CHARGING, False),
                     1, (Chargemode.SCHEDULED_CHARGING,
                         Chargemode.INSTANT_CHARGING, False),
                     1, (Chargemode.SCHEDULED_CHARGING,
                         Chargemode.INSTANT_CHARGING, True),
                     [mock_cp1], id="cp2 is prioritised")
    ])
def test_get_chargepoints_by_mode(set_mode_tuple: Tuple[Optional[str], str, bool],
                                  charging_ev_1: int,
                                  mode_tuple_1: Tuple[str, str, bool],
                                  charging_ev_2: int,
                                  mode_tuple_2: Tuple[str, str, bool],
                                  expected_valid_chargepoints):
    # setup
    def setup_cp(cp: Chargepoint, charging_ev: int, mode_tuple: Tuple[str, str, bool]) -> Chargepoint:
        cp.data.set.charging_ev = charging_ev
        charging_ev_data = cp.data.set.charging_ev_data
        charging_ev_data.data.control_parameter.prio = mode_tuple[2]
        charging_ev_data.data.control_parameter.chargemode = mode_tuple[0]
        charging_ev_data.data.control_parameter.submode = mode_tuple[1]
        return cp
    data.data.cp_data = {"cp1": setup_cp(mock_cp1, charging_ev_1, mode_tuple_1),
                         "cp2": setup_cp(mock_cp2, charging_ev_2, mode_tuple_2)}

    # evaluation
    valid_chargepoints = filter_chargepoints.get_chargepoints_by_mode(set_mode_tuple)

    # assertion
    assert valid_chargepoints == expected_valid_chargepoints


@pytest.mark.parametrize(
    "chargepoints_of_counter, chargepoints_by_mode, expected_chargepoints",
    [
        pytest.param(["cp1", "cp2"], [mock_cp1, mock_cp2], [mock_cp1, mock_cp2], id="match all"),
        pytest.param(["cp1", "cp2"], [mock_cp1], [mock_cp1], id="match by mode"),
        pytest.param(["cp2"], [mock_cp1, mock_cp2], [mock_cp2], id="match by counter"),
        pytest.param(["cp1"], [mock_cp2], [], id="match none")
    ])
def test_get_chargepoints_by_mode_and_counter(chargepoints_of_counter: List[str],
                                              chargepoints_by_mode: List[Chargepoint],
                                              expected_chargepoints: List[Chargepoint],
                                              monkeypatch):
    # setup
    get_chargepoints_of_counter_mock = Mock(return_value=chargepoints_of_counter)
    monkeypatch.setattr(CounterAll, "get_chargepoints_of_counter", get_chargepoints_of_counter_mock)
    get_chargepoints_by_mode_mock = Mock(return_value=chargepoints_by_mode)
    monkeypatch.setattr(filter_chargepoints, "get_chargepoints_by_mode", get_chargepoints_by_mode_mock)
    data.data.counter_all_data = CounterAll()

    # evaluation
    valid_chargepoints = filter_chargepoints.get_chargepoints_by_mode_and_counter(Mock(), "counter6")

    # assertion
    assert valid_chargepoints == expected_chargepoints


@pytest.mark.parametrize(
    "submode_1, submode_2, expected_chargepoints",
    [
        pytest.param(Chargemode.PV_CHARGING, Chargemode.PV_CHARGING, [mock_cp2, mock_cp1]),
        pytest.param(Chargemode.SCHEDULED_CHARGING, Chargemode.PV_CHARGING, [mock_cp2]),
        pytest.param(Chargemode.SCHEDULED_CHARGING, Chargemode.INSTANT_CHARGING, []),
    ])
def test_get_chargepoints_submode_pv_charging(submode_1: Chargemode,
                                              submode_2: Chargemode,
                                              expected_chargepoints: List[Chargepoint]):
    # setup
    def setup_cp(cp: Chargepoint, submode: str) -> Chargepoint:
        cp.data.set.charging_ev = Ev(0)
        charging_ev_data = cp.data.set.charging_ev_data
        charging_ev_data.data.control_parameter.submode = submode
        return cp
    data.data.cp_data = {"cp1": setup_cp(mock_cp1, submode_1),
                         "cp2": setup_cp(mock_cp2, submode_2)}

    # evaluation
    chargepoints = filter_chargepoints.get_chargepoints_pv_charging()

    # assertion
    assert chargepoints == expected_chargepoints
