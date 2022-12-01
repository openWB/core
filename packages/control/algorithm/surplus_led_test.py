from typing import List
from unittest.mock import Mock
import pytest

from control.algorithm import surplus_led
from control.algorithm.surplus_led import SurplusLed
from control.chargepoint import Chargepoint, ChargepointData, Get, Set
from control.ev import ChargeTemplate, Ev


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
    cp_with_feed_in, cp_without_feed_in = SurplusLed().filter_by_feed_in_limit([cp1, cp2, cp3])
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
    cp.data = ChargepointData(get=Get(currents=[15]*3))
    monkeypatch.setattr(Chargepoint, "set_state_and_log", Mock())

    # execution
    current = SurplusLed()._limit_adjust_current(cp, new_current)
    # evaluation
    assert current == expected_current


@pytest.mark.parametrize("phases, required_currents, expected_currents",
                         [
                             pytest.param(1, [10, 0, 0], [32, 0, 0]),
                             pytest.param(1, [0, 15, 0], [0, 32, 0]),
                             pytest.param(3, [10]*3, [16]*3),
                         ])
def test_set_required_current_to_max(phases: int,
                                     required_currents: List[float],
                                     expected_currents: List[int],
                                     monkeypatch):
    # setup
    ev = Ev(0)
    ev.data.control_parameter.phases = phases
    ev.data.control_parameter.required_currents = required_currents
    mock_cp1.data = ChargepointData(set=Set(charging_ev_data=ev))
    mock_get_chargepoints_surplus_led = Mock(return_value=[mock_cp1])
    monkeypatch.setattr(surplus_led, "get_chargepoints_surplus_led", mock_get_chargepoints_surplus_led)

    # execution
    SurplusLed().set_required_current_to_max()

    # evaluation
    assert mock_cp1.data.set.charging_ev_data.data.control_parameter.required_currents == expected_currents
