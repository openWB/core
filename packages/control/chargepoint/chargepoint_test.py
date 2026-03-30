from dataclasses import dataclass
from typing import List, Optional
from unittest.mock import Mock
import pytest

from control import data
from control.chargelog import chargelog
from control.chargepoint.chargepoint import Chargepoint
from control.chargepoint.chargepoint_state import ChargepointState
from control.chargepoint.chargepoint_template import CpTemplate
from control.counter import Counter
from control.ev.ev import Ev
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.manual.config import ManualSoc
from modules.vehicles.manual.soc import create_vehicle as create_manual_vehicle
from modules.vehicles.tesla.config import TeslaSoc
from modules.vehicles.tesla.soc import create_vehicle as create_tesla_vehicle


@pytest.fixture()
def mock_data() -> None:
    data.data_init(Mock())


@pytest.mark.parametrize("phase_1, phases, expected_required_currents",
                         [
                             (0, 1, [6]*3),
                             (1, 1, [6, 0, 0]),
                             (2, 2, [0, 6, 6]),
                             (3, 2, [6, 0, 6]),
                             (3, 3, [6, 6, 6]),
                         ])
def test_get_raw_currents_left_min_current(phase_1: int, phases: int, expected_required_currents: List[float]):
    # setup
    cp = Chargepoint(0, None)
    cp.data.config.phase_1 = phase_1
    cp.data.control_parameter.phases = phases

    # evaluation
    cp.set_required_currents(6)

    # assertion
    assert cp.data.control_parameter.required_currents == expected_required_currents


@pytest.mark.parametrize("required_current, phases, expected_required_current",
                         [
                             pytest.param(12, 1, 12, id="1-phasig, keine Überschreitung"),
                             pytest.param(17, 1, 16, id="1-phasig, Überschreitung des Maximalstroms"),
                             pytest.param(12, 3, 12, id="3-phasig, keine Überschreitung"),
                             pytest.param(21, 3, 20, id="1-phasig, Überschreitung des Maximalstroms"),
                             pytest.param(21, 2, 20, id="2-phasig, Überschreitung des Maximalstroms"),
                         ])
def test_check_min_max_current(required_current, phases, expected_required_current, monkeypatch):
    # setup
    cp = Chargepoint(0, None)
    cp.template = CpTemplate()
    cp.template.data.max_current_multi_phases = 20
    cp.template.data.max_current_single_phase = 16
    mock_ev_check_min_max_current = Mock(return_value=[required_current, None])
    monkeypatch.setattr(Ev, "check_min_max_current", mock_ev_check_min_max_current)
    # evaluation
    ret = cp.check_min_max_current(required_current, phases)

    # assertion
    assert ret == expected_required_current


@dataclass
class Params:
    name: str
    state: ChargepointState = ChargepointState.CHARGING_ALLOWED
    set_current: float = 0
    set_current_prev: float = 0
    phases_to_use: int = 1
    phases_in_use: int = 1
    control_parameter_phases: int = 1
    charge_state: bool = True
    failed_phase_switches: int = 0
    retry_failed_phase_switches: bool = False
    phase_switch_required: bool = False


params = [
    # PV-Laden
    Params(
        name="Wartezeit",
        state=ChargepointState.SWITCH_ON_DELAY,
        charge_state=False,
        phase_switch_required=False
    ),
    Params(
        name="Einschalten nach Wartzeit, Umschaltung erforderlich",
        state=ChargepointState.WAIT_FOR_USING_PHASES,
        phases_to_use=3,
        phases_in_use=3,
        control_parameter_phases=1,
        set_current=6,
        charge_state=False,
        phase_switch_required=True
    ),
    Params(
        name="Einschalten nach Wartzeit, keine Umschaltung erforderlich",
        state=ChargepointState.WAIT_FOR_USING_PHASES,
        phases_to_use=3,
        phases_in_use=3,
        control_parameter_phases=3,
        set_current=6,
        charge_state=False,
        phase_switch_required=False
    ),
    Params(
        name="keine Umschaltung während Warten auf Phasennutzung",
        state=ChargepointState.WAIT_FOR_USING_PHASES,
        phases_to_use=1,
        phases_in_use=3,
        control_parameter_phases=1,
        set_current=6,
        set_current_prev=6,
        charge_state=True,
        phase_switch_required=False
    ),
    Params(
        name="Umschaltung, wenn sich während der Ladung die Phasenvorgabe ändert",
        state=ChargepointState.CHARGING_ALLOWED,
        phases_to_use=3,
        phases_in_use=3,
        control_parameter_phases=1,
        set_current=6,
        set_current_prev=6,
        charge_state=True,
        phase_switch_required=True
    ),
]


@pytest.mark.parametrize("params", params, ids=[p.name for p in params])
def test_is_phase_switch_required(params: Params):
    # setup
    cp = Chargepoint(0, None)
    cp.data.control_parameter.state = params.state
    cp.data.set.current = params.set_current
    cp.data.set.current_prev = params.set_current_prev
    cp.data.set.phases_to_use = params.phases_to_use
    cp.data.get.phases_in_use = params.phases_in_use
    cp.data.control_parameter.phases = params.control_parameter_phases
    cp.data.get.charge_state = params.charge_state
    cp.data.control_parameter.failed_phase_switches = params.failed_phase_switches
    data.data_init(Mock())
    data.data.general_data.data.chargemode_config.pv_charging.retry_failed_phase_switches = (
        params.retry_failed_phase_switches
    )

    # evaluation
    ret = cp._is_phase_switch_required()

    # assertion
    assert ret == params.phase_switch_required


@pytest.mark.parametrize(
    "soc_module, reset_after_unplug, expected_calls, expected_pub_call",
    [
        pytest.param(None, None, 0, None, id="kein SoC-Modul"),
        pytest.param(create_manual_vehicle(ManualSoc(), 0), True, 1,
                     ("openWB/set/vehicle/0/soc_module/calculated_soc_state/manual_soc", 0),
                     id="manuelles SoC-Modul, Reset nach Abstecken"),
        pytest.param(create_manual_vehicle(ManualSoc(), 0), False, 0, None,
                     id="manuelles SoC-Modul, kein Reset nach Abstecken"),
        pytest.param(create_tesla_vehicle(TeslaSoc(), 0), None, 0, None, id="Tesla SoC-Modul"),
    ])
def test_process_charge_stop_reset_manual_soc(soc_module: Optional[ConfigurableVehicle],
                                              reset_after_unplug: Optional[bool],
                                              expected_calls: int,
                                              expected_pub_call: Optional[tuple],
                                              mock_pub: Mock, mock_data, monkeypatch):
    # setup
    cp = Chargepoint(0, None)
    cp.template = CpTemplate()
    cp.data.config.ev = 0
    cp.data.set.plug_state_prev = True
    ev = Ev(0)
    ev.soc_module = soc_module
    if soc_module and soc_module.vehicle_config.type == "manual":
        ev.soc_module.vehicle_config.configuration.reset_after_unplug = reset_after_unplug
    cp.data.set.charging_ev_data = ev
    data.data.ev_data["ev0"] = ev
    monkeypatch.setattr(chargelog, "save_and_reset_data", Mock())
    monkeypatch.setattr(data.data.counter_all_data, "get_evu_counter", Mock(
        return_value=Mock(spec=Counter, reset_switch_on_off=Mock())))

    # execution
    cp._process_charge_stop()

    # evaluation
    assert len(mock_pub.method_calls) - 1 == expected_calls
    if expected_calls > 0:
        assert mock_pub.method_calls[1].args == expected_pub_call
