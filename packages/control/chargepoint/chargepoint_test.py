from dataclasses import dataclass
from typing import List, Optional
from unittest.mock import Mock
import pytest

from control import data
from control.chargelog import chargelog
from control.chargemode import Chargemode
from control.chargepoint.charging_type import ChargingType
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


@pytest.mark.parametrize("required_current, max_discharge_power, dc_max_current, expected_required_current",
                         [
                             pytest.param(-50, -30000, 25, -25,
                                          id="Entladung durch CP-Hardwaregrenze begrenzt"),
                             pytest.param(-10, -30000, 25, -10,
                                          id="Entladung innerhalb der CP-Hardwaregrenze"),
                         ])
def test_check_min_max_current_bidi_discharge_respects_cp_hardware_limit(
        required_current, max_discharge_power, dc_max_current, expected_required_current):
    """ Beim Entladen (BIDI_CHARGING, required_current < 0) muss die eigene Hardware-Stromgrenze des
    Ladepunkts (dc_max_current) genauso durchgesetzt werden wie beim Laden - vor diesem Fix wurde
    check_cp_max_current() im Entlade-Zweig gar nicht aufgerufen (siehe #3795). """
    # setup
    cp = Chargepoint(0, None)
    cp.template = CpTemplate()
    cp.template.data.charging_type = ChargingType.DC.value
    cp.template.data.dc_max_current = dc_max_current
    cp.data.control_parameter.submode = Chargemode.BIDI_CHARGING
    cp.data.get.max_discharge_power = max_discharge_power

    # evaluation
    ret = cp.check_min_max_current(required_current, 1)

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
    data.data.general_data.data.chargemode_config.surplus.vehicle.retry_failed_phase_switches = (
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


@pytest.mark.parametrize(
    "chargemode_selected, min_soc, soc, charging_type, expected_min_current",
    [
        pytest.param(Chargemode.PV_CHARGING, 50, 30, ChargingType.AC.value, 16,
                     id="PV-Laden, unterhalb Mindest-SoC (AC): Mindest-SoC-Ladestrom als Untergrenze"),
        pytest.param(Chargemode.PV_CHARGING, 50, 30, ChargingType.DC.value, 145,
                     id="PV-Laden, unterhalb Mindest-SoC (DC): Mindest-SoC-Ladestrom als Untergrenze"),
        pytest.param(Chargemode.PV_CHARGING, 50, 80, ChargingType.AC.value, 6,
                     id="PV-Laden, Mindest-SoC bereits erreicht: allgemeiner Mindeststrom des Fahrzeugs"),
        pytest.param(Chargemode.PV_CHARGING, 0, 30, ChargingType.AC.value, 6,
                     id="PV-Laden, Mindest-SoC deaktiviert: allgemeiner Mindeststrom des Fahrzeugs"),
        pytest.param(Chargemode.PV_CHARGING, 50, None, ChargingType.AC.value, 6,
                     id="PV-Laden, kein SoC bekannt: allgemeiner Mindeststrom des Fahrzeugs"),
        pytest.param(Chargemode.PV_CHARGING, 50, 80, ChargingType.DC.value, 100,
                     id="PV-Laden, Mindest-SoC bereits erreicht (DC): allgemeiner Mindeststrom des Fahrzeugs"),
        pytest.param(Chargemode.INSTANT_CHARGING, 50, 30, ChargingType.AC.value, 6,
                     id="Sofortladen, Mindest-SoC-Werte vorhanden aber anderer Lademodus: unberührt"),
    ])
def test_set_control_parameter_min_soc_current_as_phase_switch_floor(
        chargemode_selected, min_soc, soc, charging_type, expected_min_current, mock_data):
    """ Mindest-SoC-Ladestrom statt allgemeinem Mindeststrom als Untergrenze für auto_phase_switch(). """
    # setup
    cp = Chargepoint(0, None)
    cp.template = CpTemplate()
    cp.template.data.charging_type = charging_type
    ev = Ev(0)
    ev.ev_template.data.min_current = 6
    ev.ev_template.data.dc_min_current = 100
    ev.data.get.soc = soc
    cp.data.set.charging_ev_data = ev
    cp.data.set.charge_template.data.chargemode.selected = chargemode_selected
    cp.data.set.charge_template.data.chargemode.pv_charging.min_soc = min_soc
    cp.data.set.charge_template.data.chargemode.pv_charging.min_soc_current = 16
    cp.data.set.charge_template.data.chargemode.pv_charging.dc_min_soc_current = 145

    # execution
    cp.set_control_parameter(Chargemode.INSTANT_CHARGING)

    # evaluation
    assert cp.data.control_parameter.min_current == expected_min_current


@pytest.mark.parametrize(
    "state",
    [
        pytest.param(ChargepointState.PHASE_SWITCH_DELAY, id="Umschaltverzögerung läuft"),
        pytest.param(ChargepointState.PERFORMING_PHASE_SWITCH, id="Umschaltung wird gerade durchgeführt"),
        pytest.param(ChargepointState.WAIT_FOR_USING_PHASES, id="wartet auf Nutzung der neuen Phasenzahl"),
    ])
def test_set_control_parameter_min_current_frozen_during_phase_switch(state, mock_data):
    """ min_current darf sich während einer laufenden Phasenumschaltung nicht ändern, sonst verfälscht das
    die reservierte Leistung in auto_phase_switch(). """
    # setup
    cp = Chargepoint(0, None)
    cp.template = CpTemplate()
    cp.template.data.charging_type = ChargingType.AC.value
    ev = Ev(0)
    ev.ev_template.data.min_current = 6
    ev.data.get.soc = 30  # noch unterhalb Mindest-SoC beim Start der Umschaltung
    cp.data.set.charging_ev_data = ev
    cp.data.set.charge_template.data.chargemode.selected = Chargemode.PV_CHARGING
    cp.data.set.charge_template.data.chargemode.pv_charging.min_soc = 50
    cp.data.set.charge_template.data.chargemode.pv_charging.min_soc_current = 16

    # Umschaltung auslösen, dabei greift die Mindest-SoC-Untergrenze
    cp.set_control_parameter(Chargemode.INSTANT_CHARGING)
    assert cp.data.control_parameter.min_current == 16

    # Umschaltung läuft nun, Mindest-SoC wird währenddessen erreicht
    cp.data.control_parameter.state = state
    ev.data.get.soc = 60

    # execution
    cp.set_control_parameter(Chargemode.INSTANT_CHARGING)

    # evaluation: min_current bleibt eingefroren, solange die Umschaltung läuft
    assert cp.data.control_parameter.min_current == 16

    # nach Abschluss der Umschaltung darf min_current wieder aktualisiert werden
    cp.data.control_parameter.state = ChargepointState.CHARGING_ALLOWED
    cp.set_control_parameter(Chargemode.INSTANT_CHARGING)
    assert cp.data.control_parameter.min_current == 6
