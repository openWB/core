from typing import Optional
from unittest.mock import Mock

import pytest

from control.chargepoint.control_parameter import ControlParameter
from control.ev.ev import Ev
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
