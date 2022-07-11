import threading
import pytest
from typing import List, Optional
from unittest.mock import Mock

from control.pv import PvAll
from control.bat import BatAll
from control.general import General
from control.ev import ChargeTemplate, Ev, EvTemplate
from control import ev
from control import data


@pytest.fixture
def vehicle() -> Ev:
    vehicle = Ev(0)
    vehicle.data["config"] = ev.get_vehicle_default()
    vehicle.ev_template = EvTemplate(0)
    vehicle.ev_template.data = ev.get_ev_template_default()
    vehicle.charge_template = ChargeTemplate(0)
    vehicle.charge_template.data = ev.get_charge_template_default()
    return vehicle


@pytest.fixture(autouse=True)
def data_module() -> None:
    data.data_init(threading.Event())
    data.data.general_data["general"] = General()
    data.data.general_data["general"].data = {"chargemode_config": {"pv_charging": {"phase_switch_delay": 7}}}
    data.data.pv_data["all"] = PvAll()
    data.data.bat_data["all"] = BatAll()


class Params:
    def __init__(self,
                 name: str,
                 max_current_one_phase: int,
                 timestamp_auto_phase_switch: Optional[str],
                 phases_to_use: int,
                 required_current: float,
                 available_power: int,
                 reserved_evu_overhang: int,
                 get_currents: List[float],
                 get_power: float,
                 expected_phases_to_use: int,
                 expected_current: float,
                 expected_message: Optional[str] = None,
                 expected_timestamp_auto_phase_switch: Optional[str] = None) -> None:
        self.name = name
        self.max_current_one_phase = max_current_one_phase
        self.timestamp_auto_phase_switch = timestamp_auto_phase_switch
        self.phases_to_use = phases_to_use
        self.required_current = required_current
        self.available_power = available_power
        self.reserved_evu_overhang = reserved_evu_overhang
        self.get_currents = get_currents
        self.get_power = get_power
        self.expected_phases_to_use = expected_phases_to_use
        self.expected_current = expected_current
        self.expected_message = expected_message
        self.expected_timestamp_auto_phase_switch = expected_timestamp_auto_phase_switch


cases = [
    Params("1to3, enough power, start timer", max_current_one_phase=16, timestamp_auto_phase_switch=None,
           phases_to_use=1, required_current=6, available_power=800, reserved_evu_overhang=0, get_currents=[15, 0, 0],
           get_power=3450, expected_phases_to_use=1, expected_current=6,
           expected_message="Umschaltverzögerung von 1 auf 3 Phasen für 7.0 Min aktiv.",
           expected_timestamp_auto_phase_switch="05/16/2022, 08:40:52"),
    Params("1to3, not enough power, start timer", max_current_one_phase=16, timestamp_auto_phase_switch=None,
           phases_to_use=1, required_current=6, available_power=300, reserved_evu_overhang=0, get_currents=[15, 0, 0],
           get_power=3450, expected_phases_to_use=1, expected_current=6),
    Params("1to3, enough power, timer not expired", max_current_one_phase=16,
           timestamp_auto_phase_switch="05/16/2022, 08:35:52", phases_to_use=1, required_current=6,
           available_power=1200, reserved_evu_overhang=460, get_currents=[15, 0, 0], get_power=3450,
           expected_phases_to_use=1, expected_current=6,
           expected_message="Umschaltverzögerung von 1 auf 3 Phasen für 7.0 Min aktiv.",
           expected_timestamp_auto_phase_switch="05/16/2022, 08:40:52"),
    Params("1to3, not enough power, timer not expired", max_current_one_phase=16,
           timestamp_auto_phase_switch="05/16/2022, 08:35:52", phases_to_use=1, required_current=6,
           available_power=440, reserved_evu_overhang=460, get_currents=[15, 0, 0], get_power=3450,
           expected_phases_to_use=1, expected_current=6,
           expected_message="Umschaltverzögerung von 1 auf 3 Phasen abgebrochen.",
           expected_timestamp_auto_phase_switch="05/16/2022, 08:40:52"),
    Params("1to3, enough power, timer expired", max_current_one_phase=16,
           timestamp_auto_phase_switch="05/16/2022, 08:32:52", phases_to_use=1, required_current=6,
           available_power=1200, reserved_evu_overhang=460, get_currents=[15, 0, 0], get_power=3450,
           expected_phases_to_use=3, expected_current=6),

    Params("3to1, not enough power, start timer", max_current_one_phase=16, timestamp_auto_phase_switch=None,
           phases_to_use=3, required_current=6, available_power=-100, reserved_evu_overhang=0,
           get_currents=[4.5, 4.4, 5.8], get_power=3381, expected_phases_to_use=3, expected_current=6,
           expected_message="Umschaltverzögerung von 3 auf 1 Phasen für 9.0 Min aktiv.",
           expected_timestamp_auto_phase_switch="05/16/2022, 08:40:52"),
    Params("3to1, not enough power, timer not expired", max_current_one_phase=16,
           timestamp_auto_phase_switch="05/16/2022, 08:35:52",
           phases_to_use=3, required_current=6, available_power=-100, reserved_evu_overhang=-460,
           get_currents=[4.5, 4.4, 5.8], get_power=3381, expected_phases_to_use=3, expected_current=6,
           expected_message="Umschaltverzögerung von 3 auf 1 Phasen für 9.0 Min aktiv.",
           expected_timestamp_auto_phase_switch="05/16/2022, 08:40:52"),
    Params("3to1, enough power, timer not expired", max_current_one_phase=16,
           timestamp_auto_phase_switch="05/16/2022, 08:35:52", phases_to_use=3, required_current=6,
           available_power=860, reserved_evu_overhang=-460, get_currents=[4.5, 4.4, 5.8],
           get_power=3381, expected_phases_to_use=3, expected_current=6,
           expected_message="Umschaltverzögerung von 3 auf 1 Phasen abgebrochen.",
           expected_timestamp_auto_phase_switch="05/16/2022, 08:40:52"),
    Params("3to1, not enough power, timer expired", max_current_one_phase=16,
           timestamp_auto_phase_switch="05/16/2022, 08:29:52", phases_to_use=3, required_current=6,
           available_power=-100, reserved_evu_overhang=-460, get_currents=[4.5, 4.4, 5.8],
           get_power=3381, expected_phases_to_use=1, expected_current=16),
]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_auto_phase_switch(monkeypatch, vehicle: Ev, params: Params):
    # setup
    mock_power_for_bat_charging = Mock(name="power_for_bat_charging", return_value=0)
    monkeypatch.setattr(data.data.bat_data["all"], "power_for_bat_charging", mock_power_for_bat_charging)

    vehicle.ev_template.data["max_current_one_phase"] = params.max_current_one_phase
    vehicle.data["control_parameter"]["timestamp_auto_phase_switch"] = params.timestamp_auto_phase_switch
    vehicle.data["control_parameter"]["phases"] = params.phases_to_use
    vehicle.data["control_parameter"]["required_current"] = params.required_current
    data.data.pv_data["all"].data["set"]["available_power"] = params.available_power
    data.data.pv_data["all"].data["set"]["reserved_evu_overhang"] = params.reserved_evu_overhang

    # execution
    phases_to_use, current, message = vehicle.auto_phase_switch(0, params.get_currents, params.get_power)

    # evaluation
    assert phases_to_use == params.expected_phases_to_use
    assert current == params.expected_current
    assert message == params.expected_message
