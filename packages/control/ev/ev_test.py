from typing import Optional
from unittest.mock import Mock

import pytest

from control import data

from control.chargepoint.chargepoint_state import ChargepointState
from control.chargepoint.control_parameter import ControlParameter
from control.ev.ev import Ev, get_ev_to_rfid
from control.limiting_value import LimitingValue, LoadmanagementLimit
from helpermodules import timecheck
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.vehicles.mqtt.config import MqttSocSetup
from modules.vehicles.mqtt.soc import create_vehicle


@pytest.mark.parametrize(
    "check_timestamp, charge_state, soc_request_timestamp, expected_request_soc",
    [pytest.param(False, False, None, True, id="no soc_request_timestamp"),
     pytest.param(True, False, 100, False, id="not charging, not expired"),
     pytest.param(False, False, 100, True, id="not charging, expired"),
     pytest.param(True, True, 100, False, id="charging, not expired"),
     pytest.param(False, True, 100, True, id="charging, expired"),
     ])
def test_soc_interval_expired(check_timestamp: bool,
                              charge_state: bool,
                              soc_request_timestamp: Optional[float],
                              expected_request_soc: bool,
                              monkeypatch):
    # setup
    ev = Ev(0)
    ev.soc_module = create_vehicle(MqttSocSetup(), 0)
    ev.data.get.soc_request_timestamp = soc_request_timestamp
    check_timestamp_mock = Mock(return_value=check_timestamp)
    monkeypatch.setattr(timecheck, "check_timestamp", check_timestamp_mock)

    # execution
    request_soc = ev.soc_interval_expired(VehicleUpdateData(charge_state=charge_state))

    # evaluation
    assert request_soc == expected_request_soc


@pytest.mark.parametrize(
    "timestamp_last_phase_switch, timestamp_phase_switch_buffer_start, expected_result",
    [
        pytest.param(1652682881, None, (False, "30 Sek."), id="Puffer abgelaufen, Wartezeit noch nicht gestartet"),
        pytest.param(1652682881, 1652683232, (False, "10 Sek."), id="Puffer abgelaufen, Wartezeit gestartet"),
        pytest.param(1652682881, 1652683212, (True, None), id="Puffer abgelaufen, Wartezeit abgelaufen"),
        pytest.param(1652682962, None, (False, "30 Sek."),
                     id="Puffer noch nicht abgelaufen, Wartezeit länger, Wartezeit noch nicht gestartet"),
        pytest.param(1652682962, 1652683237, (False, "15 Sek."),
                     id="Puffer noch nicht abgelaufen, Wartezeit länger, Wartezeit gestartet"),
        pytest.param(1652682932, 1652683220, (True, None),
                     id="Puffer noch nicht abgelaufen, Wartezeit länger, Wartezeit abgelaufen"),
        pytest.param(1652683132, None, (False, "3 Min."), id="Puffer noch nicht abgelaufen, Puffer länger, abwarten"),
        pytest.param(1652682950, 1652682972, (True, None),
                     id="Puffer noch nicht abgelaufen, Puffer länger, abgelaufen"),
    ],
)
def test_remaining_phase_switch_time(timestamp_last_phase_switch,
                                     timestamp_phase_switch_buffer_start,
                                     expected_result):
    # setup
    ev = Ev(0)
    control_parameter = ControlParameter()
    control_parameter.timestamp_last_phase_switch = timestamp_last_phase_switch
    control_parameter.timestamp_phase_switch_buffer_start = timestamp_phase_switch_buffer_start

    # execution
    result = ev._remaining_phase_switch_time(
        control_parameter=control_parameter,
        waiting_time=30,
        buffer=300,
    )

    # evaluation
    assert result == expected_result


@pytest.mark.parametrize(
    "surplus, expected_condition",
    [
        pytest.param(6901, True, id="Überschuss reicht für min_current auf allen Phasen: umschalten"),
        pytest.param(5000, False, id="Überschuss reicht nicht für min_current auf allen Phasen: nicht umschalten"),
    ],
)
def test_check_phase_switch_conditions_required_surplus_based_on_min_current(surplus, expected_condition):
    """ required_surplus muss auf control_parameter.min_current basieren. """
    # setup
    ev = Ev(0)
    ev.ev_template.data.max_phases = 3
    ev.ev_template.data.max_current_single_phase = 16
    ev.ev_template.data.nominal_difference = 1
    control_parameter = ControlParameter()
    control_parameter.min_current = 10
    control_parameter.phases = 1
    control_parameter.required_current = 6
    limit = LoadmanagementLimit(message=None, limiting_value=LimitingValue.CURRENT)

    # execution
    condition, _ = ev._check_phase_switch_conditions(
        control_parameter=control_parameter,
        evse_current=0,
        get_currents=[0, 0, 0],
        get_power=0,
        max_current_cp=32,
        limit=limit,
        surplus=surplus,
    )

    # evaluation: required_surplus = min_current(10) * max_phases(3) * 230 = 6900
    assert condition == expected_condition


def test_reset_phase_switch_delay_uses_reserved_power_not_a_fresh_calculation(monkeypatch):
    """ reset_phase_switch_delay() muss die beim Reservieren gespeicherte Leistung zurücknehmen, nicht neu
    berechnen - sonst würde reserved_surplus driften, falls sich zB max_phases inzwischen geändert hat. """
    # setup
    ev = Ev(0)
    ev.ev_template.data.max_current_single_phase = 16
    control_parameter = ControlParameter()
    control_parameter.state = ChargepointState.PHASE_SWITCH_DELAY
    control_parameter.phases = 1
    control_parameter.reserved_power = 500
    evu_counter = Mock()
    evu_counter.data.set.reserved_surplus = 1000
    monkeypatch.setattr(data.data.counter_all_data, "get_evu_counter", Mock(return_value=evu_counter))

    # execution
    ev.reset_phase_switch_delay(control_parameter)

    # evaluation
    assert evu_counter.data.set.reserved_surplus == 500
    assert control_parameter.reserved_power == 0
    assert control_parameter.state == ChargepointState.CHARGING_ALLOWED


@pytest.fixture(autouse=True)
def data_module() -> None:
    data.data_init(Mock())
    ev10 = Ev(10)
    ev11 = Ev(11)
    ev12 = Ev(12)
    ev13 = Ev(13)
    ev14 = Ev(14)
    ev15 = Ev(15)
    ev10.data.tag_id = ["0815", "abcxyz"]
    ev11.data.tag_id = ["aa:bb:cc:dd:ee:ff", "abc*"]
    ev12.data.tag_id = ["123*", "abc?"]
    ev13.data.tag_id = ["234?"]
    ev14.data.tag_id = ["aa:aa:aa*"]
    ev15.data.tag_id = ["bb:bb:bb:??:??:??"]
    data.data.ev_data = {"ev10": ev10, "ev11": ev11, "ev12": ev12, "ev13": ev13, "ev14": ev14, "ev15": ev15}


@pytest.mark.parametrize(
    "rfid, vehicle_id, expected_result",
    [
        pytest.param("0815", None, 10),
        pytest.param(None, "aa:bb:cc:dd:ee:ff", 11),
        pytest.param("1239", None, 12),
        pytest.param("1234231cxv23ds23", None, 12),
        pytest.param("2345", None, 13),
        pytest.param("2348", None, 13),
        pytest.param("23489", None, None),
        pytest.param("aa:aa:aa124a", None, 14),
        pytest.param("aa:aa:aa:bb:bb:bb", None, 14),
        pytest.param("bb:bb:bb:ca:bc:de", None, 15),
        pytest.param("bb:bb:ba:ca:bc:de", None, None),
        pytest.param("abcxyz", None, 10),
        pytest.param("unknownTag", None, None),
        pytest.param(None, "unknownID", None),
    ],
)
def test_ev_identification(rfid, vehicle_id, expected_result):
    # setup

    # execution
    result = get_ev_to_rfid(rfid, vehicle_id)

    # evaluation
    assert result == expected_result
