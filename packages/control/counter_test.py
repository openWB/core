from dataclasses import dataclass
from typing import List, Optional
from unittest.mock import Mock
import pytest

from control import data
from control.chargepoint import Chargepoint
from control.counter import Counter
from control.ev import ChargeTemplate, Ev
from control.general import General
from control.state_machine import StateMachine
from modules.common.fault_state import FaultStateLevel


@pytest.fixture
def general_data_fixture() -> None:
    data.data_init(Mock())
    data.data.general_data = General()


@pytest.mark.parametrize("fault_state, expected_loadmanagement_available",
                         [pytest.param(FaultStateLevel.ERROR, False),
                          pytest.param(FaultStateLevel.NO_ERROR, True)])
def test_set_loadmanagement_state(fault_state: FaultStateLevel,
                                  expected_loadmanagement_available: bool,
                                  monkeypatch,
                                  data_):
    # setup
    connected_cps_mock = Mock(return_value=["cp3", "cp4"])
    monkeypatch.setattr(data.data.counter_all_data, "get_chargepoints_of_counter", connected_cps_mock)
    counter = Counter(0)
    counter.data.get.fault_state = fault_state

    # execution
    counter._set_loadmanagement_state()

    # evaluation
    assert data.data.cp_data["cp3"].data.set.loadmanagement_available == expected_loadmanagement_available
    assert data.data.cp_data["cp4"].data.set.loadmanagement_available == expected_loadmanagement_available


@pytest.mark.parametrize("raw_currents_left, expected_max_exceeding",
                         [pytest.param([32, 32, 15], [0]*3, id="not exceeded"),
                          pytest.param([32, 35, 18], [0]*3, id="not exceeded with export"),
                          pytest.param([38, 55, 39], [0]*3, id="not exceeded with export two phases"),
                          pytest.param([32, 32, 13], [0, 0, 1], id="exceeded on one phase"),
                          pytest.param([29, 11, 8], [0, 0, 3], id="exceeded on two phases"),
                          pytest.param([35, 11, 8], [0, 6, 9], id="exceeded on two phases with export")])
def test_get_unbalanced_load_exceeding(raw_currents_left: List[float],
                                       expected_max_exceeding: List[float],
                                       monkeypatch,
                                       general_data_fixture):
    # setup
    get_evu_counter_mock = Mock(return_value="counter0")
    monkeypatch.setattr(data.data.counter_all_data, "get_evu_counter_str", get_evu_counter_mock)
    counter = Counter(0)
    counter.data.config.max_currents = [32]*3
    data.data.general_data.data.chargemode_config.unbalanced_load = True

    # execution
    max_exceeding = counter.get_unbalanced_load_exceeding(raw_currents_left)

    # evaluation
    assert max_exceeding == expected_max_exceeding


@pytest.mark.parametrize("max_currents, expected_raw_currents_left",
                         [pytest.param([40]*3, [40, 0, 10], id="Überbelastung"),
                          ([60]*3, [60, 15, 30])])
def test_set_current_left(max_currents: List[float],
                          expected_raw_currents_left: List[float],
                          monkeypatch,
                          data_):
    # setup
    get_chargepoints_of_counter_mock = Mock(return_value=["cp3", "cp4", "cp5"])
    monkeypatch.setattr(data.data.counter_all_data, "get_chargepoints_of_counter", get_chargepoints_of_counter_mock)
    counter = Counter(0)
    counter.data.config.max_currents = max_currents
    counter.data.get.currents = [55]*3

    # execution
    counter._set_current_left()

    # evaluation
    assert counter.data.set.raw_currents_left == expected_raw_currents_left


@dataclass
class Params:
    name: str
    feed_in_limit: bool
    reserved_surplus: float
    surplus: float
    threshold: float
    timestamp_switch_on_off: Optional[str]
    state: StateMachine
    expected_msg: Optional[str]
    expected_timestamp_switch_on_off: Optional[str]
    expected_reserved_surplus: float


cases = [
    Params("Einschaltschwelle wurde unterschritten, Timer zurücksetzen", False, 1500, 119,
           1500, '05/16/2022, 08:40:50', StateMachine.SWITCH_ON_DELAY,
           Counter.SWITCH_ON_FALLEN_BELOW.format(1500), None, 0),
    Params("Timer starten", False, 0, 1501, 1500, None, StateMachine.NO_CHARGING_ALLOWED,
           Counter.SWITCH_ON_WAITING.format(30), '05/16/2022, 08:40:52', 1500),
    Params("Einschaltschwelle nicht erreicht", False, 0, 1499, 1500,
           None, StateMachine.NO_CHARGING_ALLOWED, Counter.SWITCH_ON_NOT_EXCEEDED.format(1500), None, 0),
    Params("Einschaltschwelle läuft", False, 1500, 121, 1500,
           '05/16/2022, 08:40:50', StateMachine.SWITCH_ON_DELAY, None, '05/16/2022, 08:40:50', 1500),
    Params("Feed_in_limit, Einschaltschwelle wurde unterschritten, Timer zurücksetzen", True, 15000,
           13619, 15000, '05/16/2022, 08:40:50', StateMachine.SWITCH_ON_DELAY,
           Counter.SWITCH_ON_FALLEN_BELOW.format(1500), None, 0),
    Params("Feed_in_limit, Timer starten", True, 0, 15001, 15000, None, StateMachine.NO_CHARGING_ALLOWED,
           Counter.SWITCH_ON_WAITING.format(30), '05/16/2022, 08:40:52', 15000),
    Params("Feed_in_limit, Einschaltschwelle nicht erreicht", True, 0, 14999,
           15000, None, StateMachine.NO_CHARGING_ALLOWED, Counter.SWITCH_ON_NOT_EXCEEDED.format(1500), None, 0),
    Params("Feed_in_limit, Einschaltschwelle läuft", True, 1500, 15001,
           15000, '05/16/2022, 08:40:50', StateMachine.SWITCH_ON_DELAY, None, '05/16/2022, 08:40:50', 1500),
]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_switch_on_threshold_reached(params: Params, caplog, general_data_fixture, monkeypatch):
    # setup
    c = Counter(0)
    c.data.set.reserved_surplus = params.reserved_surplus
    cp = Chargepoint(0, None)
    ev = Ev(0)
    ev.data.control_parameter.phases = 1
    ev.data.control_parameter.state = params.state
    ev.data.control_parameter.timestamp_switch_on_off = params.timestamp_switch_on_off
    ev.data.charge_template = ChargeTemplate(0)
    ev.data.charge_template.data.chargemode.pv_charging.feed_in_limit = params.feed_in_limit
    cp.data.set.charging_ev_data = ev
    mock_calc_switch_on_power = Mock(return_value=[params.surplus, params.threshold])
    monkeypatch.setattr(Counter, "calc_switch_on_power", mock_calc_switch_on_power)

    # execution
    c.switch_on_threshold_reached(cp)

    # evaluation
    assert c.data.set.reserved_surplus == params.expected_reserved_surplus
    assert params.expected_msg is None or params.expected_msg in caplog.text
    assert (cp.data.set.charging_ev_data.data.control_parameter.timestamp_switch_on_off ==
            params.expected_timestamp_switch_on_off)


@pytest.mark.parametrize("control_range, expected_available_power",
                         [pytest.param([0, 230], 1115, id="Bezug"),
                          pytest.param([-230, 0], 885, id="Einspeisung")],
                         )
def test_control_range(control_range, expected_available_power, general_data_fixture):
    # setup
    data.data.general_data.data.chargemode_config.pv_charging.control_range = control_range
    c = Counter(0)

    # execution
    available_power = c._control_range(1000)

    # evaluation
    assert available_power == expected_available_power
