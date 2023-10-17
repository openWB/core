import threading
import pytest
from typing import List, Optional
from unittest.mock import Mock
from control.chargepoint.control_parameter import ControlParameter
from control.counter import Counter, CounterData, Set

from control.pv_all import PvAll
from control.bat_all import BatAll
from control.general import General
from control.ev import Ev
from control import data
from control.chargepoint.chargepoint_state import ChargepointState


@pytest.fixture
def vehicle() -> Ev:
    vehicle = Ev(0)
    return vehicle


@pytest.fixture(autouse=True)
def data_module() -> None:
    data.data_init(threading.Event())
    data.data.general_data = General()
    data.data.pv_all_data = PvAll()
    data.data.bat_all_data = BatAll()


class Params:
    def __init__(self,
                 name: str,
                 max_current_single_phase: int,
                 timestamp_auto_phase_switch: Optional[str],
                 phases_to_use: int,
                 required_current: float,
                 evu_surplus: int,
                 reserved_evu_overhang: int,
                 get_currents: List[float],
                 get_power: float,
                 state: ChargepointState,
                 expected_phases_to_use: int,
                 expected_current: float,
                 expected_state: ChargepointState,
                 expected_message: Optional[str] = None,
                 expected_timestamp_auto_phase_switch: Optional[str] = None) -> None:
        self.name = name
        self.max_current_single_phase = max_current_single_phase
        self.timestamp_auto_phase_switch = timestamp_auto_phase_switch
        self.phases_to_use = phases_to_use
        self.required_current = required_current
        self.available_power = evu_surplus
        self.reserved_evu_overhang = reserved_evu_overhang
        self.get_currents = get_currents
        self.get_power = get_power
        self.state = state
        self.expected_phases_to_use = expected_phases_to_use
        self.expected_current = expected_current
        self.expected_state = expected_state
        self.expected_message = expected_message
        self.expected_timestamp_auto_phase_switch = expected_timestamp_auto_phase_switch


cases = [
    Params("1to3, enough power, start timer", max_current_single_phase=16, timestamp_auto_phase_switch=None,
           phases_to_use=1, required_current=6, evu_surplus=-800, reserved_evu_overhang=0, get_currents=[15.6, 0, 0],
           get_power=3450, state=ChargepointState.CHARGING_ALLOWED, expected_phases_to_use=1, expected_current=6,
           expected_message="Umschaltverzögerung von 1 auf 3 Phasen für 7.0 Min aktiv.",
           expected_timestamp_auto_phase_switch="05/16/2022, 08:40:52",
           expected_state=ChargepointState.PHASE_SWITCH_DELAY),
    Params("1to3, not enough power, start timer", max_current_single_phase=16, timestamp_auto_phase_switch=None,
           phases_to_use=1, required_current=6, evu_surplus=-300, reserved_evu_overhang=0, get_currents=[15.6, 0, 0],
           get_power=3450, state=ChargepointState.CHARGING_ALLOWED, expected_phases_to_use=1, expected_current=6,
           expected_state=ChargepointState.CHARGING_ALLOWED),
    Params("1to3, enough power, timer not expired", max_current_single_phase=16,
           timestamp_auto_phase_switch="05/16/2022, 08:35:52", phases_to_use=1, required_current=6,
           evu_surplus=-1200, reserved_evu_overhang=460, get_currents=[15.6, 0, 0], get_power=3450,
           state=ChargepointState.PHASE_SWITCH_DELAY, expected_phases_to_use=1, expected_current=6,
           expected_message="Umschaltverzögerung von 1 auf 3 Phasen für 7.0 Min aktiv.",
           expected_timestamp_auto_phase_switch="05/16/2022, 08:40:52",
           expected_state=ChargepointState.PHASE_SWITCH_DELAY),
    Params("1to3, not enough power, timer not expired", max_current_single_phase=16,
           timestamp_auto_phase_switch="05/16/2022, 08:35:52", phases_to_use=1, required_current=6,
           evu_surplus=0, reserved_evu_overhang=460, get_currents=[15.6, 0, 0], get_power=3450,
           state=ChargepointState.PHASE_SWITCH_DELAY, expected_phases_to_use=1, expected_current=6,
           expected_message=f"Umschaltverzögerung von 1 auf 3 Phasen abgebrochen{Ev.NOT_ENOUGH_POWER}",
           expected_timestamp_auto_phase_switch="05/16/2022, 08:40:52",
           expected_state=ChargepointState.CHARGING_ALLOWED),
    Params("1to3, enough power, timer expired", max_current_single_phase=16,
           timestamp_auto_phase_switch="05/16/2022, 08:32:52", phases_to_use=1, required_current=6,
           evu_surplus=-1200, reserved_evu_overhang=460, get_currents=[15.6, 0, 0], get_power=3450,
           state=ChargepointState.PHASE_SWITCH_DELAY,
           expected_phases_to_use=3, expected_current=6, expected_state=ChargepointState.PHASE_SWITCH_DELAY_EXPIRED),

    Params("3to1, not enough power, start timer", max_current_single_phase=16, timestamp_auto_phase_switch=None,
           phases_to_use=3, required_current=6, evu_surplus=0, reserved_evu_overhang=0,
           get_currents=[4.5, 4.4, 5.8], get_power=3381, state=ChargepointState.CHARGING_ALLOWED,
           expected_phases_to_use=3, expected_current=6,
           expected_message="Umschaltverzögerung von 3 auf 1 Phasen für 9.0 Min aktiv.",
           expected_timestamp_auto_phase_switch="05/16/2022, 08:40:52",
           expected_state=ChargepointState.PHASE_SWITCH_DELAY),
    Params("3to1, not enough power, timer not expired", max_current_single_phase=16,
           timestamp_auto_phase_switch="05/16/2022, 08:35:52",
           phases_to_use=3, required_current=6, evu_surplus=0, reserved_evu_overhang=-460,
           get_currents=[4.5, 4.4, 5.8], get_power=3381, state=ChargepointState.PHASE_SWITCH_DELAY,
           expected_phases_to_use=3, expected_current=6,
           expected_message="Umschaltverzögerung von 3 auf 1 Phasen für 9.0 Min aktiv.",
           expected_timestamp_auto_phase_switch="05/16/2022, 08:40:52",
           expected_state=ChargepointState.PHASE_SWITCH_DELAY),
    Params("3to1, enough power, timer not expired", max_current_single_phase=16,
           timestamp_auto_phase_switch="05/16/2022, 08:35:52", phases_to_use=3, required_current=6,
           evu_surplus=-860, reserved_evu_overhang=0, get_currents=[4.5, 4.4, 5.8],
           get_power=3381, state=ChargepointState.PHASE_SWITCH_DELAY, expected_phases_to_use=3, expected_current=6,
           expected_message=f"Umschaltverzögerung von 3 auf 1 Phasen abgebrochen{Ev.ENOUGH_POWER}",
           expected_timestamp_auto_phase_switch="05/16/2022, 08:40:52",
           expected_state=ChargepointState.CHARGING_ALLOWED),
    Params("3to1, not enough power, timer expired", max_current_single_phase=16,
           timestamp_auto_phase_switch="05/16/2022, 08:29:52", phases_to_use=3, required_current=6,
           evu_surplus=0, reserved_evu_overhang=-460, get_currents=[4.5, 4.4, 5.8],
           get_power=3381, state=ChargepointState.PHASE_SWITCH_DELAY, expected_phases_to_use=1, expected_current=16,
           expected_state=ChargepointState.PHASE_SWITCH_DELAY_EXPIRED),
]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_auto_phase_switch(monkeypatch, vehicle: Ev, params: Params):
    # setup
    mock_evu = Mock(spec=Counter, data=Mock(spec=CounterData,
                                            set=Mock(spec=Set, reserved_surplus=params.reserved_evu_overhang,
                                                     released_surplus=0)))
    mock_get_evu_counter = Mock(name="power_for_bat_charging", return_value=mock_evu)
    monkeypatch.setattr(data.data.counter_all_data, "get_evu_counter", mock_get_evu_counter)
    mock_evu_counter_surplus = Mock(return_value=params.available_power)
    monkeypatch.setattr(mock_evu, "calc_surplus", mock_evu_counter_surplus)

    vehicle.ev_template.data.max_current_single_phase = params.max_current_single_phase
    control_parameter = ControlParameter()
    control_parameter.timestamp_auto_phase_switch = params.timestamp_auto_phase_switch
    control_parameter.phases = params.phases_to_use
    control_parameter.required_current = params.required_current
    control_parameter.state = params.state

    # execution
    phases_to_use, current, message = vehicle.auto_phase_switch(control_parameter,
                                                                0,
                                                                params.get_currents,
                                                                params.get_power,
                                                                32,
                                                                3,
                                                                None)

    # evaluation
    assert phases_to_use == params.expected_phases_to_use
    assert current == params.expected_current
    assert message == params.expected_message
    assert control_parameter.state == params.expected_state
