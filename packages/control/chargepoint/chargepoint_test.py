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
from ocpp.v16.enums import ChargePointStatus


@pytest.fixture()
def mock_data() -> None:
    data.data_init(Mock())


@pytest.mark.parametrize("availability,controller_status,connector_status", [
    ([True, True], ChargePointStatus.available, ChargePointStatus.preparing),
    ([True, False], ChargePointStatus.available, ChargePointStatus.unavailable),
    ([False, True], ChargePointStatus.unavailable, ChargePointStatus.unavailable),
    ([False, False], ChargePointStatus.unavailable, ChargePointStatus.unavailable),
])
def test_ocpp_availability_status_and_permission(
    mock_data, monkeypatch, availability, controller_status, connector_status
):
    cp = Chargepoint(1, None)
    cp.data.config.ocpp_chargebox_id = "box-1"
    data.data.optional_data.data.ocpp.config.active = True
    cp.data.get.ocpp.connected = True
    cp.data.get.ocpp.tag_accepted = True
    cp.data.get.ocpp.availability = availability
    cp.data.get.plug_state = True
    assert cp.get_ocpp_status_connector_0() == controller_status
    assert cp.get_ocpp_status() == connector_status
    assert cp._is_ocpp()[0] is all(availability)
    notification = Mock()
    monkeypatch.setattr(data.data.ocpp_client, "status_notification", notification)
    cp.ocpp_send_status_notification()
    assert [request.kwargs["connector_id"] for request in notification.call_args_list] == [0, 1]
    assert [request.kwargs["status"] for request in notification.call_args_list] == [
        controller_status, connector_status]


@pytest.mark.parametrize("local_block,local_message", [
    (None, None),
    ("manual", "Keine Ladung, da der Ladepunkt gesperrt ist."),
    ("grid", "Ladepunkt gesperrt, da der Netzschutz aktiv ist."),
    ("unplugged", "Keine Ladung, da kein Auto angesteckt ist."),
    ("autolock", "Keine Ladung, da Sperren nach Uhrzeit aktiv ist."),
])
@pytest.mark.parametrize("ocpp_state,ocpp_message", [
    ("ready", None),
    ("disabled", None),
    ("disconnected", "Keine Ladung: Verbindung zum OCPP-Server fehlt."),
    ("unconfirmed", "Keine Ladung: Startbestätigung vom OCPP-Server fehlt. "
                    "Stecker abziehen und erneut verbinden."),
])
def test_charging_permission_combines_local_and_ocpp_messages(
    mock_data, monkeypatch, local_block, local_message, ocpp_state, ocpp_message
):
    cp = Chargepoint(1, None)
    cp.template = CpTemplate()
    cp.data.config.ocpp_chargebox_id = "box-1"
    cp.data.get.plug_state = local_block != "unplugged"
    cp.data.set.manual_lock = local_block == "manual"
    general = data.data.general_data.data
    general.grid_protection_configured = local_block == "grid"
    general.grid_protection_active = local_block == "grid"
    general.grid_protection_timestamp = None
    data.data.optional_data.data.rfid.active = False
    monkeypatch.setattr(cp.template, "is_locked_by_autolock", lambda _: local_block == "autolock")
    data.data.optional_data.data.ocpp.config.active = ocpp_state != "disabled"
    cp.data.get.ocpp.connected = ocpp_state != "disconnected"
    cp.data.get.ocpp.tag_accepted = True
    if ocpp_state == "unconfirmed":
        cp.data.get.ocpp.authorization_flow_status = "start_unconfirmed"

    possible, message = cp.is_charging_possible()

    assert possible is (local_block is None and ocpp_message is None)
    assert message == (" ".join(text for text in (local_message, ocpp_message) if text) or None)


@pytest.mark.parametrize("plugged,tag_source,expected", [
    (False, None, None),
    (False, "scan", None),
    (True, None, "Keine Ladung: RFID zur OCPP-Freigabe erforderlich."),
    (True, "scan", "Warte auf OCPP-Transaktionsfreigabe."),
    (True, "assigned", "Warte auf OCPP-Transaktionsfreigabe."),
    (True, "vehicle", "Warte auf OCPP-Transaktionsfreigabe."),
])
@pytest.mark.parametrize("flow_status", [None, "accepted"])
def test_ocpp_wait_message_preserves_charging_block(mock_data, plugged, tag_source, expected, flow_status):
    cp = Chargepoint(1, None)
    cp.template = CpTemplate()
    cp.data.config.ocpp_chargebox_id = "box-1"
    data.data.optional_data.data.ocpp.config.active = True
    cp.data.get.ocpp.connected = True
    cp.data.get.ocpp.authorization_flow_status = flow_status
    cp.data.get.plug_state = plugged
    if tag_source == "scan":
        cp.data.get.rfid = "TAG"
    elif tag_source == "assigned":
        cp.data.set.rfid = "TAG"
    elif tag_source == "vehicle":
        cp.data.get.vehicle_id = "TAG"

    assert cp._is_ocpp() == (False, expected)
    possible, message = cp.is_charging_possible()
    assert possible is False
    assert message == (expected if plugged else "Keine Ladung, da kein Auto angesteckt ist.")


@pytest.mark.parametrize("plugged", [False, True])
@pytest.mark.parametrize("flow_status,expected", [
    ("init", "RFID-Autorisierung am OCPP-Server läuft."),
    ("start_pending", "OCPP-Transaktionstart wird vorbereitet."),
    ("start_authorizing", "RFID-Autorisierung am OCPP-Server läuft."),
    ("start_starting", "RFID akzeptiert. OCPP-Transaktion wird gestartet."),
    ("start_rejected", "Keine Ladung: OCPP Authorisierung abgelehnt."),
    ("start_error", "Keine Ladung: Fehler beim OCPP-Transaktionstart."),
])
def test_ocpp_specific_message_takes_priority_over_wait_message(mock_data, plugged, flow_status, expected):
    cp = Chargepoint(1, None)
    cp.data.config.ocpp_chargebox_id = "box-1"
    data.data.optional_data.data.ocpp.config.active = True
    cp.data.get.ocpp.connected = True
    cp.data.get.ocpp.authorization_flow_status = flow_status
    cp.data.get.plug_state = plugged
    cp.data.get.rfid = "TAG"

    assert cp._is_ocpp() == (False, expected)


@pytest.mark.parametrize("stop_flag", ["remote_stop", "reset", "unlock_stop", "rfid_stop"])
@pytest.mark.parametrize("plugged,transaction_id,charging,current,expected", [
    (True, None, False, 0, ChargePointStatus.finishing),
    (False, None, False, 0, ChargePointStatus.available),
    (True, 42, True, 6, ChargePointStatus.charging),
    (True, 42, False, 0, ChargePointStatus.suspended_evse),
    (True, 42, False, 6, ChargePointStatus.suspended_ev),
    (True, None, True, 6, ChargePointStatus.preparing),
])
def test_ocpp_stop_status_requires_local_transaction_and_charging_to_end(
    stop_flag, plugged, transaction_id, charging, current, expected
):
    cp = Chargepoint(1, None)
    setattr(cp.data.get.ocpp, stop_flag, True)
    cp.data.get.ocpp.transaction_id = transaction_id
    cp.data.get.plug_state = plugged
    cp.data.get.charge_state = charging
    cp.data.set.current = current

    assert cp.get_ocpp_status() == expected


@pytest.mark.parametrize("availability", [[True, True], [True, False], [False, True], [False, False]])
@pytest.mark.parametrize("stop_flag", ["remote_stop", "reset", "unlock_stop", "rfid_stop"])
def test_ocpp_fault_has_priority_over_availability_and_stop_flags(availability, stop_flag):
    cp = Chargepoint(1, None)
    cp.data.get.fault_state = 2
    cp.data.get.ocpp.availability = availability
    setattr(cp.data.get.ocpp, stop_flag, True)

    assert cp.get_ocpp_status_connector_0() == ChargePointStatus.faulted
    assert cp.get_ocpp_status() == ChargePointStatus.faulted


@pytest.mark.parametrize("availability,plugged,transaction_id,charging,current,stop,expected", [
    ([True, True], False, None, False, 0, False, ChargePointStatus.available),
    ([True, True], True, None, False, 0, False, ChargePointStatus.preparing),
    ([True, True], True, 42, True, 6, False, ChargePointStatus.charging),
    ([True, True], True, 42, False, 0, False, ChargePointStatus.suspended_evse),
    ([True, True], True, 42, False, 6, False, ChargePointStatus.suspended_ev),
    ([True, True], True, None, False, 0, True, ChargePointStatus.finishing),
    ([True, False], True, None, False, 0, False, ChargePointStatus.unavailable),
    ([False, True], True, None, False, 0, False, ChargePointStatus.unavailable),
])
def test_ocpp_warning_preserves_operating_status(
    availability, plugged, transaction_id, charging, current, stop, expected
):
    cp = Chargepoint(1, None)
    cp.data.get.fault_state = 1
    cp.data.get.ocpp.availability = availability
    cp.data.get.plug_state = plugged
    cp.data.get.ocpp.transaction_id = transaction_id
    cp.data.get.charge_state = charging
    cp.data.set.current = current
    cp.data.get.ocpp.remote_stop = stop

    assert cp.get_ocpp_status() == expected
    assert cp.get_ocpp_status_connector_0() == (
        ChargePointStatus.available if availability[0] else ChargePointStatus.unavailable
    )


def test_ocpp_freshly_plugged_vehicle_without_transaction_is_preparing():
    cp = Chargepoint(1, None)
    cp.data.get.plug_state = True

    assert cp.get_ocpp_status() == ChargePointStatus.preparing


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


@pytest.mark.parametrize("state_prev, expected_message_present",
                         [
                             pytest.param(ChargepointState.SWITCH_ON_DELAY, True,
                                          id="Ladestart nach Einschaltverzoegerung: CP-Unterbrechung noetig"),
                             pytest.param(ChargepointState.NO_CHARGING_ALLOWED, True,
                                          id="regulaerer Ladestart: CP-Unterbrechung noetig"),
                             pytest.param(ChargepointState.PERFORMING_PHASE_SWITCH, False,
                                          id="direkt nach Phasenumschaltung: keine zusaetzliche CP-Unterbrechung"),
                         ])
def test_initiate_control_pilot_interruption_uses_state_prev_not_state(state_prev, expected_message_present):
    """ WAIT_FOR_USING_PHASES wird nicht nur direkt nach einer echten Phasenumschaltung erreicht, sondern
    zB auch direkt nach Ablauf der Einschaltverzoegerung (siehe Discussion #3908, lackylacky) - dort war
    dann also nach jedem PV-Ladestart mit reiner Ein-Phasen-Ladung (kein hw_supports_phase_switch())
    dauerhaft keine Control-Pilot-Unterbrechung mehr moeglich. state_prev unterscheidet die beiden
    Faelle korrekt, state (aktuell WAIT_FOR_USING_PHASES in beiden Faellen) nicht. """
    # setup
    cp = Chargepoint(0, None)
    cp.chargepoint_module = Mock(interrupt_cp=Mock(), config=Mock(id=0))
    cp.data.set.charging_ev_data = Ev(0)
    cp.data.set.charging_ev_data.ev_template.data.control_pilot_interruption = True
    cp.data.set.charging_ev_data.ev_template.data.control_pilot_interruption_duration = 4
    cp.data.set.charging_ev_data.ev_template.data.control_pilot_interruption_retry_interval = 0
    cp.data.config.control_pilot_interruption_hw = True
    # state_prev ueber remember_previous_values() setzen statt direkt zuzuweisen
    cp.data.set.current = 0
    cp.data.control_parameter.state = state_prev
    cp.remember_previous_values()
    # aktueller Zyklus: Ladung startet
    cp.data.control_parameter.state = ChargepointState.WAIT_FOR_USING_PHASES
    cp.data.set.current = 6

    # evaluation
    cp.initiate_control_pilot_interruption()

    # assertion
    message_present = (cp.data.get.state_str is not None and
                       "Control-Pilot-Unterbrechung" in cp.data.get.state_str)
    assert message_present == expected_message_present


def test_initiate_control_pilot_interruption_skipped_when_phase_switch_pending():
    """ Kontaktoren stehen noch auf falscher Phasenzahl -> initiate_phase_switch() schaltet im selben
    Zyklus bereits CP um, keine zusaetzliche Unterbrechung noetig. """
    # setup
    cp = Chargepoint(0, None)
    cp.chargepoint_module = Mock(interrupt_cp=Mock(), config=Mock(id=0))
    cp.data.set.charging_ev_data = Ev(0)
    cp.data.set.charging_ev_data.ev_template.data.control_pilot_interruption = True
    cp.data.set.charging_ev_data.ev_template.data.control_pilot_interruption_duration = 4
    cp.data.set.charging_ev_data.ev_template.data.control_pilot_interruption_retry_interval = 0
    cp.data.config.control_pilot_interruption_hw = True
    cp.data.set.current = 0
    cp.data.control_parameter.state = ChargepointState.SWITCH_ON_DELAY
    cp.remember_previous_values()
    cp.data.control_parameter.state = ChargepointState.WAIT_FOR_USING_PHASES
    cp.data.set.current = 6
    # Kontaktoren (1p) weichen von der benoetigten Phasenzahl (3p) ab
    cp.data.set.phases_to_use = 3
    cp.data.control_parameter.phases = 1

    # evaluation
    cp.initiate_control_pilot_interruption()

    # assertion
    message_present = (cp.data.get.state_str is not None and
                       "Control-Pilot-Unterbrechung" in cp.data.get.state_str)
    assert message_present is False


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
