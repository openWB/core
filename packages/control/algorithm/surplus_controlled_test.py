from typing import List
from unittest.mock import Mock
import pytest

from control import data
from control.algorithm import surplus_controlled
from control.algorithm.filter_chargepoints import get_loads_by_chargemodes
from control.algorithm.surplus_controlled import (CONSIDERED_CHARGE_MODES_PV_ONLY, SurplusControlled,
                                                  limit_adjust_current)
from control.chargemode import Chargemode
from control.chargepoint.chargepoint import Chargepoint, ChargepointData
from control.chargepoint.chargepoint_data import Get, Set
from control.chargepoint.chargepoint_state import ChargepointState
from control.chargepoint.chargepoint_template import CpTemplate
from control.chargepoint.control_parameter import ControlParameter
from control.counter_all.counter_all import CounterAll
from control.ev.ev import Ev


@pytest.fixture(autouse=True)
def init_data_store():
    data.data_init(Mock())


@pytest.fixture(autouse=True)
def mock_cp1() -> Chargepoint:
    return Chargepoint(1, None)


@pytest.fixture(autouse=True)
def mock_cp2() -> Chargepoint:
    return Chargepoint(2, None)


@pytest.fixture(autouse=True)
def mock_cp3() -> Chargepoint:
    return Chargepoint(3, None)


@pytest.fixture(autouse=True)
def mock_data() -> None:
    data.data_init(Mock())
    data.data.counter_all_data = CounterAll()


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
    current = limit_adjust_current(cp, new_current)
    # evaluation
    assert current == expected_current


@pytest.mark.parametrize("phases, required_currents, expected_currents",
                         [
                             pytest.param(1, [10, 0, 0], [16, 0, 0]),
                             pytest.param(1, [0, 15, 0], [0, 16, 0]),
                             pytest.param(3, [10]*3, [16]*3),
                             pytest.param(3, [0]*3, [0]*3),
                         ])
def test_set_required_current_to_max(phases: int,
                                     required_currents: List[float],
                                     expected_currents: List[int],
                                     monkeypatch,
                                     mock_cp1: Chargepoint):
    # setup
    ev = Ev(0)
    mock_cp1.data = ChargepointData(set=Set(charging_ev_data=ev),
                                    control_parameter=ControlParameter(phases=phases,
                                                                       required_current=max(required_currents),
                                                                       required_currents=required_currents))
    mock_cp1.template = CpTemplate()
    mock_get_chargepoints_surplus_controlled = Mock(return_value=[mock_cp1])
    monkeypatch.setattr(surplus_controlled, "get_loads_by_chargemodes",
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
        pytest.param(12.5, 12.5, 12.0, id="Auto lädt mit 0.5A Abweichung von der Soll-Stromstärke"),
        pytest.param(11.8, 11.8, 10.600000000000001, id="Auto lädt mit mehr als Soll-Stromstärke"),
        pytest.param(14.2, 14.2, 15.399999999999999,
                     id="Auto lädt mit weniger als Soll-Stromstärke, "
                        "diff kleiner als max_current_change, aber EVSE-Begrenzung ist nicht erreicht."),
        pytest.param(14.5, 14.2, 15.7,
                     id="Auto lädt mit weniger als Soll-Stromstärke, "
                        "diff größer als max_current_change, aber EVSE-Begrenzung ist nicht erreicht."),
        pytest.param(15, 15, 16,
                     id="Auto lädt mit weniger als Soll-Stromstärke, aber EVSE-Begrenzung ist erreicht.")
    ])
def test_add_unused_evse_current(evse_current: float,
                                 limited_current: float,
                                 expected_current: float):
    # setup
    c = Chargepoint(0, None)
    c.data.get.charge_state = True
    c.data.get.currents = [13]*3
    c.data.get.evse_current = evse_current
    c.data.control_parameter.required_current = 16
    c.data.set.current = limited_current

    # execution
    SurplusControlled()._fix_deviating_evse_current(c)

    # evaluation
    assert c.data.set.current == expected_current


@pytest.mark.parametrize(
    "submode_1, submode_2, expected_cp_keys",
    [
        pytest.param(Chargemode.PV_CHARGING, Chargemode.PV_CHARGING, ["cp1", "cp2"]),
        pytest.param(Chargemode.INSTANT_CHARGING, Chargemode.PV_CHARGING, ["cp2"]),
        pytest.param(Chargemode.INSTANT_CHARGING, Chargemode.INSTANT_CHARGING, []),
    ])
def test_get_chargepoints_submode_pv_charging(submode_1: Chargemode,
                                              submode_2: Chargemode,
                                              expected_cp_keys: List[str],
                                              mock_cp1: Chargepoint,
                                              mock_cp2: Chargepoint):
    # setup
    def setup_cp(cp: Chargepoint, submode: str) -> Chargepoint:
        cp.data = ChargepointData()
        cp.data.set.charging_ev_data = Ev(cp.num)
        cp.data.config.ev = cp.num
        cp.data.control_parameter.chargemode = Chargemode.PV_CHARGING
        cp.data.control_parameter.submode = submode
        cp.data.control_parameter.required_current = 6
        return cp
    data.data.cp_data = {"cp1": setup_cp(mock_cp1, submode_1),
                         "cp2": setup_cp(mock_cp2, submode_2)}
    expected_chargepoints = [data.data.cp_data[key] for key in expected_cp_keys]
    data.data.counter_all_data = CounterAll()
    data.data.counter_all_data.data.get.loadmanagement_prios = [{"type": "vehicle", "id": 1},
                                                                {"type": "vehicle", "id": 2}]

    # evaluation
    chargepoints = get_loads_by_chargemodes(CONSIDERED_CHARGE_MODES_PV_ONLY)

    # assertion
    assert chargepoints == expected_chargepoints


@pytest.mark.parametrize(
    "is_buffer_depleted, expected_switch_off_checked",
    [
        pytest.param(True, True,
                     id="Puffer leer -> Abschaltschwelle greift trotz möglicher Rückschaltung"),
        pytest.param(False, False,
                     id="Puffer nicht leer -> Rückschaltung hat wie bisher Vorrang"),
    ])
def test_check_submode_pv_charging_buffer_depleted(is_buffer_depleted: bool,
                                                   expected_switch_off_checked: bool,
                                                   mock_cp1: Chargepoint,
                                                   monkeypatch):
    # setup: dreiphasig ladender LP im Automatikmodus, dessen Hardware umschalten kann
    mock_cp1.data = ChargepointData()
    mock_cp1.data.set.charging_ev_data = Ev(1)
    mock_cp1.data.config.ev = 1
    mock_cp1.data.control_parameter.chargemode = Chargemode.PV_CHARGING
    mock_cp1.data.control_parameter.submode = Chargemode.PV_CHARGING
    mock_cp1.data.control_parameter.state = ChargepointState.CHARGING_ALLOWED
    mock_cp1.data.control_parameter.template_phases = 0
    mock_cp1.data.get.phases_in_use = 3
    monkeypatch.setattr(Chargepoint, "cp_state_hw_support_phase_switch", Mock(return_value=True))
    data.data.cp_data = {"cp1": mock_cp1}
    data.data.counter_all_data.data.get.loadmanagement_prios = [{"type": "vehicle", "id": 1}]
    switch_off_check_threshold_mock = Mock()
    evu_counter_mock = Mock(switch_off_check_threshold=switch_off_check_threshold_mock)
    monkeypatch.setattr(data.data.counter_all_data, "get_evu_counter", Mock(return_value=evu_counter_mock))
    monkeypatch.setattr(data.data.bat_all_data, "is_buffer_depleted", Mock(return_value=is_buffer_depleted))

    # execution
    SurplusControlled().check_submode_pv_charging()

    # evaluation
    assert switch_off_check_threshold_mock.called == expected_switch_off_checked
