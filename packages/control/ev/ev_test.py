from typing import List, Optional, Tuple
from unittest.mock import Mock

import pytest

from control import data

from control.chargemode import Chargemode
from control.chargepoint.control_parameter import ControlParameter
from control.limiting_value import LoadmanagementLimit
from control.ev.ev import Ev, get_ev_to_rfid
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


@pytest.mark.parametrize(
    "phases, submode, currents, surplus, is_buffering, expected_result",
    [
        pytest.param(3, Chargemode.PV_CHARGING, [6, 6, 6], -500, True, (False, Ev.BAT_BUFFERING),
                     id="Speicher puffert -> keine Rückschaltung 3 -> 1"),
        pytest.param(3, Chargemode.PV_CHARGING, [6, 6, 6], -500, False, (True, None),
                     id="Speicher puffert nicht -> Rückschaltung 3 -> 1 wie bisher"),
        pytest.param(1, Chargemode.PV_CHARGING, [16, 0, 0], 5000, True, (True, None),
                     id="Speicher puffert, Hochschaltung 1 -> 3 bleibt unberührt"),
        pytest.param(3, Chargemode.INSTANT_CHARGING, [6, 6, 6], -500, True, (True, None),
                     id="kein Überschuss-Laden -> Sperre greift nicht"),
    ])
def test_check_phase_switch_conditions_bat_buffering(phases: int,
                                                     submode: Chargemode,
                                                     currents: List[float],
                                                     surplus: float,
                                                     is_buffering: bool,
                                                     expected_result: Tuple[bool, Optional[str]],
                                                     monkeypatch):
    # setup
    ev = Ev(0)
    control_parameter = ControlParameter()
    control_parameter.phases = phases
    control_parameter.submode = submode
    control_parameter.min_current = 6
    control_parameter.required_current = 6
    monkeypatch.setattr(data.data.bat_all_data, "is_buffering", Mock(return_value=is_buffering))

    # execution
    result = ev._check_phase_switch_conditions(control_parameter,
                                               evse_current=6,
                                               get_currents=currents,
                                               get_power=sum(currents) * 230,
                                               max_current_cp=16,
                                               limit=LoadmanagementLimit(None, None),
                                               surplus=surplus)

    # evaluation
    assert result == expected_result
