from typing import List
from unittest.mock import Mock
import pytest

from control import data
from control.algorithm import surplus_controlled
from control.algorithm.filter_chargepoints import get_chargepoints_by_chargemodes
from control.algorithm.surplus_controlled import CONSIDERED_CHARGE_MODES_PV_ONLY, SurplusControlled
from control.chargemode import Chargemode
from control.chargepoint.chargepoint import Chargepoint, ChargepointData
from control.chargepoint.chargepoint_data import Get, Set
from control.chargepoint.chargepoint_template import CpTemplate
from control.chargepoint.control_parameter import ControlParameter
from control.ev.charge_template import ChargeTemplate
from control.ev.ev import Ev


@pytest.fixture(autouse=True)
def mock_cp1() -> Chargepoint:
    return Chargepoint(1, None)


@pytest.fixture(autouse=True)
def mock_cp2() -> Chargepoint:
    return Chargepoint(2, None)


@pytest.fixture(autouse=True)
def mock_cp3() -> Chargepoint:
    return Chargepoint(3, None)


@pytest.mark.parametrize("feed_in_limit_1, feed_in_limit_2, feed_in_limit_3, expected_sorted",
                         [pytest.param(True, True, True, ([mock_cp1, mock_cp2, mock_cp3], [])),
                          pytest.param(True, False, True, ([mock_cp1, mock_cp3], [mock_cp2])),
                          pytest.param(False, False, False, ([], [mock_cp1, mock_cp2, mock_cp3]))])
def test_filter_by_feed_in_limit(feed_in_limit_1: bool,
                                 feed_in_limit_2: bool,
                                 feed_in_limit_3: bool,
                                 expected_sorted: int):
    # setup
    def setup_cp(cp: Chargepoint, feed_in_limit: bool) -> Chargepoint:
        ev = Ev(0)
        ev.charge_template = ChargeTemplate(0)
        ev.charge_template.data.chargemode.pv_charging.feed_in_limit = feed_in_limit
        cp.data = ChargepointData(set=Set(charging_ev_data=ev))
        return cp

    cp1 = setup_cp(mock_cp1, feed_in_limit_1)
    cp2 = setup_cp(mock_cp2, feed_in_limit_2)
    cp3 = setup_cp(mock_cp3, feed_in_limit_3)
    # execution
    cp_with_feed_in, cp_without_feed_in = SurplusControlled().filter_by_feed_in_limit([cp1, cp2, cp3])
    # evaluation
    assert (cp_with_feed_in, cp_without_feed_in) == expected_sorted


@pytest.mark.parametrize("new_current, expected_current",
                         [
                             pytest.param(7, 10),
                             pytest.param(12, 12),
                             pytest.param(22.1, 20),
                         ])
def test_limit_adjust_current(new_current: float, expected_current: float, monkeypatch):
    # setup
    cp = Chargepoint(0, None)
    cp.data = ChargepointData(get=Get(charge_state=True, currents=[15]*3))
    cp.template = CpTemplate()
    monkeypatch.setattr(Chargepoint, "set_state_and_log", Mock())

    # execution
    current = SurplusControlled()._limit_adjust_current(cp, new_current)
    # evaluation
    assert current == expected_current


@pytest.mark.parametrize("phases, required_currents, expected_currents",
                         [
                             pytest.param(1, [10, 0, 0], [16, 0, 0]),
                             pytest.param(1, [0, 15, 0], [0, 16, 0]),
                             pytest.param(3, [10]*3, [16]*3),
                         ])
def test_set_required_current_to_max(phases: int,
                                     required_currents: List[float],
                                     expected_currents: List[int],
                                     monkeypatch):
    # setup
    ev = Ev(0)
    mock_cp1.data = ChargepointData(set=Set(charging_ev_data=ev),
                                    control_parameter=ControlParameter(phases=phases,
                                                                       required_currents=required_currents))
    mock_cp1.template = CpTemplate()
    mock_get_chargepoints_surplus_controlled = Mock(return_value=[mock_cp1])
    monkeypatch.setattr(surplus_controlled, "get_chargepoints_by_chargemodes",
                        mock_get_chargepoints_surplus_controlled)

    # execution
    SurplusControlled().set_required_current_to_max()

    # evaluation
    assert mock_cp1.data.control_parameter.required_currents == expected_currents


@pytest.mark.parametrize(
    "evse_current, limited_current, expected_current",
    [
        pytest.param(None, 6, 6, id="Kein Soll-Strom aus der EVSE ausgelesen"),
        pytest.param(13, 13, 13, id="Auto lädt mit Soll-Stromstärke"),
        pytest.param(12.5, 12.5, 12.5, id="Auto lädt mit 0.5A Abweichung von der Soll-Stromstärke"),
        pytest.param(11.8, 11.8, 10.600000000000001, id="Auto lädt mit mehr als Soll-Stromstärke"),
        pytest.param(14.2, 14.2, 15.399999999999999, id="Auto lädt mit weniger als Soll-Stromstärke"),
        pytest.param(15, 15, 16,
                     id="Auto lädt mit weniger als Soll-Stromstärke, aber EVSE-Begrenzung ist erreicht.")
    ])
def test_add_unused_evse_current(evse_current: float,
                                 limited_current: float,
                                 expected_current: float):
    # setup
    c = Chargepoint(0, None)
    c.data.get.currents = [13]*3
    c.data.get.evse_current = evse_current
    c.data.control_parameter.required_current = 16
    c.data.set.current = limited_current

    # execution
    SurplusControlled()._fix_deviating_evse_current(c)

    # evaluation
    assert c.data.set.current == expected_current


@pytest.mark.parametrize(
    "submode_1, submode_2, expected_chargepoints",
    [
        pytest.param(Chargemode.PV_CHARGING, Chargemode.PV_CHARGING, [mock_cp1, mock_cp2]),
        pytest.param(Chargemode.INSTANT_CHARGING, Chargemode.PV_CHARGING, [mock_cp2]),
        pytest.param(Chargemode.INSTANT_CHARGING, Chargemode.INSTANT_CHARGING, []),
    ])
def test_get_chargepoints_submode_pv_charging(submode_1: Chargemode,
                                              submode_2: Chargemode,
                                              expected_chargepoints: List[Chargepoint]):
    # setup
    def setup_cp(cp: Chargepoint, submode: str) -> Chargepoint:
        cp.data.set.charging_ev = Ev(0)
        cp.data.control_parameter.chargemode = Chargemode.PV_CHARGING
        cp.data.control_parameter.submode = submode
        return cp
    data.data.cp_data = {"cp1": setup_cp(mock_cp1, submode_1),
                         "cp2": setup_cp(mock_cp2, submode_2)}

    # evaluation
    chargepoints = get_chargepoints_by_chargemodes(CONSIDERED_CHARGE_MODES_PV_ONLY)

    # assertion
    assert chargepoints == expected_chargepoints
