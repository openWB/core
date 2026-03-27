import pytest
from threading import Event
from typing import List, Optional, Tuple
from unittest.mock import Mock
from control.chargepoint.control_parameter import ControlParameter
from control.counter import Counter, CounterData, Set

from control.limiting_value import LimitingValue, LoadmanagementLimit
from control.ev.charge_template import ChargeTemplate
from control.pv_all import PvAll
from control.bat_all import BatAll
from control.general import General
from control.ev.ev import Ev
from control import data
from control.chargepoint.chargepoint_state import ChargepointState


@pytest.fixture
def vehicle() -> Ev:
    vehicle = Ev(0)
    return vehicle


@pytest.fixture(autouse=True)
def data_module() -> None:
    data.data_init(Event())
    data.data.general_data = General()
    data.data.pv_all_data = PvAll()
    data.data.bat_all_data = BatAll()


class Params:
    def __init__(self,
                 name: str,
                 max_current_single_phase: int,
                 timestamp_phase_switch_buffer_start: Optional[float],
                 phases_to_use: int,
                 required_current: float,
                 evu_surplus: int,
                 get_currents: List[float],
                 get_power: float,
                 state: ChargepointState,
                 expected_phases_to_use: int,
                 expected_current: float,
                 expected_state: ChargepointState,
                 expected_message: Optional[str] = None) -> None:
        self.name = name
        self.max_current_single_phase = max_current_single_phase
        self.timestamp_phase_switch_buffer_start = timestamp_phase_switch_buffer_start
        self.phases_to_use = phases_to_use
        self.required_current = required_current
        self.available_power = evu_surplus
        self.get_currents = get_currents
        self.get_power = get_power
        self.state = state
        self.expected_phases_to_use = expected_phases_to_use
        self.expected_current = expected_current
        self.expected_state = expected_state
        self.expected_message = expected_message


cases = [
    Params("1to3, enough power, start timer", max_current_single_phase=16, timestamp_phase_switch_buffer_start=None,
           phases_to_use=1, required_current=6, evu_surplus=800, get_currents=[15.6, 0, 0],
           get_power=3450, state=ChargepointState.CHARGING_ALLOWED, expected_phases_to_use=1, expected_current=6,
           expected_message=Ev.PHASE_SWITCH_DELAY_TEXT.format("Umschaltung von 1 auf 3", "30 Sek."),
           expected_state=ChargepointState.PHASE_SWITCH_DELAY),
    Params("1to3, not enough power, start timer", max_current_single_phase=16, timestamp_phase_switch_buffer_start=None,
           phases_to_use=1, required_current=6, evu_surplus=300, get_currents=[15.6, 0, 0],
           get_power=3450, state=ChargepointState.CHARGING_ALLOWED, expected_phases_to_use=1, expected_current=6,
           expected_state=ChargepointState.CHARGING_ALLOWED),
    Params("1to3, enough power, timer not expired", max_current_single_phase=16,
           timestamp_phase_switch_buffer_start=1652683232.0, phases_to_use=1, required_current=6,
           evu_surplus=1460, get_currents=[15.6, 0, 0], get_power=3450,
           state=ChargepointState.PHASE_SWITCH_DELAY, expected_phases_to_use=1, expected_current=6,
           expected_message=Ev.PHASE_SWITCH_DELAY_TEXT.format("Umschaltung von 1 auf 3", "10 Sek."),
           expected_state=ChargepointState.PHASE_SWITCH_DELAY),
    Params("1to3, not enough power, timer not expired", max_current_single_phase=16,
           timestamp_phase_switch_buffer_start=1652683202.0, phases_to_use=1, required_current=6,
           evu_surplus=460, get_currents=[15.6, 0, 0], get_power=3450,
           state=ChargepointState.PHASE_SWITCH_DELAY, expected_phases_to_use=1, expected_current=6,
           expected_message=f"Verzögerung für die Umschaltung von 1 auf 3 Phasen abgebrochen{Ev.NOT_ENOUGH_POWER}",
           expected_state=ChargepointState.CHARGING_ALLOWED),
    Params("1to3, enough power, timer expired", max_current_single_phase=16,
           timestamp_phase_switch_buffer_start=1652682802.0, phases_to_use=1, required_current=6,
           evu_surplus=1640, get_currents=[15.6, 0, 0], get_power=3450,
           state=ChargepointState.PHASE_SWITCH_DELAY,
           expected_phases_to_use=3, expected_current=6, expected_state=ChargepointState.PHASE_SWITCH_AWAITED),

    Params("3to1, not enough power, start timer", max_current_single_phase=16,
           timestamp_phase_switch_buffer_start=1652683202,
           phases_to_use=3, required_current=6, evu_surplus=0,
           get_currents=[4.5, 4.4, 5.8], get_power=3381, state=ChargepointState.CHARGING_ALLOWED,
           expected_phases_to_use=3, expected_current=6,
           expected_message="Umschaltung von 3 auf 1 Phasen in 10 Sek..",
           expected_state=ChargepointState.PHASE_SWITCH_DELAY),
    Params("3to1, not enough power, timer not expired", max_current_single_phase=16,
           timestamp_phase_switch_buffer_start=1652683202.0,
           phases_to_use=3, required_current=6, evu_surplus=-460,
           get_currents=[4.5, 4.4, 5.8], get_power=3381, state=ChargepointState.PHASE_SWITCH_DELAY,
           expected_phases_to_use=3, expected_current=6,
           expected_message="Umschaltung von 3 auf 1 Phasen in 10 Sek..",
           expected_state=ChargepointState.PHASE_SWITCH_DELAY),
    Params("3to1, enough power, timer not expired", max_current_single_phase=16,
           timestamp_phase_switch_buffer_start=1652683202.0, phases_to_use=3, required_current=6,
           evu_surplus=860, get_currents=[4.5, 4.4, 5.8],
           get_power=3381, state=ChargepointState.PHASE_SWITCH_DELAY, expected_phases_to_use=3, expected_current=6,
           expected_message=f"Verzögerung für die Umschaltung von 3 auf 1 Phasen abgebrochen{Ev.ENOUGH_POWER}",
           expected_state=ChargepointState.CHARGING_ALLOWED),
    Params("3to1, not enough power, timer expired", max_current_single_phase=16,
           timestamp_phase_switch_buffer_start=1652682802.0, phases_to_use=3, required_current=6,
           evu_surplus=-460, get_currents=[4.5, 4.4, 5.8],
           get_power=3381, state=ChargepointState.PHASE_SWITCH_DELAY, expected_phases_to_use=1, expected_current=16,
           expected_state=ChargepointState.PHASE_SWITCH_AWAITED),
]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_auto_phase_switch(monkeypatch, vehicle: Ev, params: Params):
    # setup
    mock_evu = Mock(spec=Counter, data=Mock(spec=CounterData,
                                            set=Mock(spec=Set, reserved_surplus=0,
                                                     released_surplus=0)))
    mock_get_evu_counter = Mock(name="power_for_bat_charging", return_value=mock_evu)
    monkeypatch.setattr(data.data.counter_all_data, "get_evu_counter", mock_get_evu_counter)
    mock_evu_counter_surplus = Mock(return_value=params.available_power)
    monkeypatch.setattr(mock_evu, "get_usable_surplus", mock_evu_counter_surplus)

    vehicle.ev_template.data.max_current_single_phase = params.max_current_single_phase
    control_parameter = ControlParameter()
    control_parameter.timestamp_last_phase_switch = 1652682802
    control_parameter.timestamp_phase_switch_buffer_start = params.timestamp_phase_switch_buffer_start
    control_parameter.phases = params.phases_to_use
    control_parameter.required_current = params.required_current
    control_parameter.state = params.state

    # execution
    phases_to_use, current, message = vehicle.auto_phase_switch(ChargeTemplate(),
                                                                control_parameter,
                                                                0,
                                                                max(params.get_currents),
                                                                params.get_currents,
                                                                params.get_power,
                                                                32,
                                                                3,
                                                                LoadmanagementLimit(None,  None))

    # evaluation
    assert phases_to_use == params.expected_phases_to_use
    assert current == params.expected_current
    assert message == params.expected_message
    assert control_parameter.state == params.expected_state


@pytest.mark.parametrize(
    "evse_current, get_currents, all_surplus, limit, expected",
    [
        pytest.param(8, [7.7]*3, 100, LoadmanagementLimit(None, None), (False, Ev.ENOUGH_POWER),
                     id="kein 1p3p, genug Leistung für mehrphasige Ladung"),
        pytest.param(10, [9.8, 0, 0], 50, LoadmanagementLimit(None, None), (False, Ev.NOT_ENOUGH_POWER),
                     id="kein 1p3p, nicht genug Leistung, um auf 3p zu schalten"),
        pytest.param(16, [14, 0, 0], 5000, LoadmanagementLimit(None, None),
                     (False, Ev.CURRENT_OUT_OF_NOMINAL_DIFFERENCE),
                     id="kein 1p3p, Auto lädt nicht mit vorgegebener Maximalstromstärke"),
        pytest.param(6, [7.5]*3, -20, LoadmanagementLimit(None, None), (False, Ev.CURRENT_OUT_OF_NOMINAL_DIFFERENCE),
                     id="kein 1p3p, Auto lädt nicht mit vorgegebener Minimalstromstärke"),
        pytest.param(16, [15.8, 0, 0], 5000, LoadmanagementLimit(None, None), (True, None), id="1p3p"),
        pytest.param(6, [5.8]*3, -10, LoadmanagementLimit(None, None), (True, None), id="3p1p"),
        pytest.param(10, [9.8, 0, 0], 5000,
                     LoadmanagementLimit(message=", da der Maximal-Strom an Zähler Test erreicht ist.",
                                         limiting_value=LimitingValue.CURRENT), (True, None),
                     id="1p3p, da durch die Begrenzung des LM nicht mit maximalem Strom geladen wird"),
        pytest.param(10, [9.8, 0, 0], 5000,
                     LoadmanagementLimit(message=", da die maximale Schieflast an Zähler Test erreicht ist.",
                                         limiting_value=LimitingValue.UNBALANCED_LOAD), (True, None),
                     id="1p3p, da durch die Begrenzung der Schieflast nicht mit maximalem Strom geladen wird"),
    ])
def test_check_phase_switch_conditions(evse_current: int,
                                       get_currents: List[float],
                                       all_surplus: int,
                                       limit: LoadmanagementLimit,
                                       expected: Tuple[bool, Optional[str]],
                                       monkeypatch):
    # setup
    ev = Ev(0)
    mock_get_evu_counter = Mock(return_value=Mock(get_usable_surplus=Mock(return_value=all_surplus)))
    monkeypatch.setattr(data.data.counter_all_data, "get_evu_counter", mock_get_evu_counter)

    # execution
    phase_switch, condition_msg = ev._check_phase_switch_conditions(
        ChargeTemplate(),
        ControlParameter(phases=3-get_currents.count(0)),
        evse_current,
        get_currents,
        sum(get_currents)*230,
        16,
        limit)

    # evaluation
    assert (phase_switch, condition_msg) == expected
