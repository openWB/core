from typing import Dict
from unittest.mock import Mock
import requests_mock

import pytest

from modules.chargepoints.openwb_pro.config import OpenWBPro, OpenWBProConfiguration
from modules.common.component_state import ChargepointState
from modules.chargepoints.openwb_pro import chargepoint_module
from modules.common.fault_state_level import FaultStateLevel
from modules.conftest import SAMPLE_IP


def sample_chargepoint_state():
    return ChargepointState(
        power=4302.7,
        powers=[1444.4, 1423.7, 1438.1],
        currents=[6.133, 6.066, 6.122],
        imported=10839,
        exported=0,
        plug_state=True,
        charge_state=True,
        phases_in_use=3,
        rfid="001180644",
        rfid_timestamp=1700839714,
        vehicle_id="98:ED:5C:B4:EE:8D",
        evse_current=6,
        serial_number="823950"
    )


def sample():
    return {'charge_state': True,
            'currents': [6.133, 6.066, 6.122],
            'date': '2023:01:30-18:48:31',
            'evse_signaling': 'fake highlevel + basic iec61851',
            'exported': 0,
            'imported': 10839,
            'offered_current': 6,
            'phases_actual': 3,
            'phases_in_use': 3,
            'phases_target': 3,
            'plug_state': True,
            'power_all': 4302.7,
            'powers': [1444.4, 1423.7, 1438.1],
            'serial': '823950',
            'timestamp': 1675104511,
            'v2g_ready': 0,
            'vehicle_id': '98:ED:5C:B4:EE:8D',
            'rfid_tag': "001180644",
            "rfid_timestamp": 1700839714}


def sample_chargepoint_extended():
    return ChargepointState(
        power=0,
        powers=[0]*3,
        currents=[0]*3,
        voltages=[230.67, 0, 0],
        imported=6827330,
        exported=0,
        plug_state=False,
        charge_state=False,
        phases_in_use=1,
        rfid=None,
        frequency=50.2,
        evse_current=6,
        serial_number="493826"
    )


def sample_extended():
    return {"date": "2023:09:18-15:13:41",
            "timestamp": 1695042821,
            "powers": [0, 0, 0],
            "power_all": 0,
            "currents": [0, 0, 0],
            "voltages": [230.67, 0, 0],
            "imported": 6827330,
            "exported": 0,
            "plug_state": False,
            "charge_state": False,
            "phases_actual": 0,
            "phases_target": 3,
            "phases_in_use": 1,
            "offered_current": 6,
            "evse_signaling": "unclear\n",
            "v2g_ready": 0,
            "soc_value": 0,
            "soc_timestamp": 0,
            "vehicle_id": None,
            "serial": "493826",
            "frequency": 50.2}


@pytest.mark.parametrize("sample_state, expected_state",
                         [pytest.param(sample(), sample_chargepoint_state()),
                          pytest.param(sample_extended(), sample_chargepoint_extended())
                          ])
def test_openwb_pro(sample_state: Dict, expected_state: Dict, monkeypatch, requests_mock: requests_mock.mock):
    # setup
    mock_chargepoint_value_store = Mock()
    monkeypatch.setattr(chargepoint_module, 'get_chargepoint_value_store',
                        Mock(return_value=mock_chargepoint_value_store))
    requests_mock.post(f'http://{SAMPLE_IP}/connect.php')
    requests_mock.get(f'http://{SAMPLE_IP}/connect.php', json=sample_state)

    cp = chargepoint_module.ChargepointModule(OpenWBPro(configuration=OpenWBProConfiguration(ip_address=SAMPLE_IP)))

    # execution
    cp.get_values()

    # evaluation
    assert vars(mock_chargepoint_value_store.set.call_args[0][0]) == vars(expected_state)


@pytest.mark.parametrize("chargepoint_state, expected_exception, expected_message", [
    (ChargepointState(charge_state=False, currents=[0, 2, 0], plug_state=True,
     power=0), ValueError, chargepoint_module.ChargepointModule.WRONG_CHARGE_STATE),
    (ChargepointState(charge_state=True, currents=[0, 0, 0], plug_state=False,
     power=30), ValueError, chargepoint_module.ChargepointModule.WRONG_PLUG_STATE),
    (ChargepointState(charge_state=True, currents=[0, 2, 0], plug_state=True, power=30), None, None)
])
def test_validate_values(chargepoint_state, expected_exception, expected_message):
    cp = chargepoint_module.ChargepointModule(OpenWBPro(configuration=OpenWBProConfiguration(ip_address=SAMPLE_IP)))
    if expected_exception is not None:
        with pytest.raises(expected_exception, match=expected_message):
            cp.validate_values(chargepoint_state)
    else:
        cp.validate_values(chargepoint_state)  # Sollte keine Ausnahme auslösen


def sample_wrong_charge_state():
    sample_wrong_charge_state = sample()
    sample_wrong_charge_state.update({'charge_state': False,
                                      'currents': [0, 2, 0],
                                      'power_all': 0,
                                      'date': '2023:01:30-18:48:31',
                                      'evse_signaling': 'fake'})
    return sample_wrong_charge_state


def sample_wrong_charge_state_chargepoint_state():
    sample_wrong_charge_state_chargepoint_state = sample_chargepoint_state()
    sample_wrong_charge_state_chargepoint_state.charge_state = False
    sample_wrong_charge_state_chargepoint_state.currents = [0, 2, 0]
    sample_wrong_charge_state_chargepoint_state.power = 0
    return sample_wrong_charge_state_chargepoint_state


def sample_chargepoint_state_resetted():
    sample_chargepoint_state_resetted = sample_wrong_charge_state_chargepoint_state()
    sample_chargepoint_state_resetted.plug_state = False
    return sample_chargepoint_state_resetted


@pytest.mark.parametrize(
    "sample_state, error_timestamp,expected_exception, expected_error_timestamp, expected_chargepoint_state", [
        pytest.param(sample(), None, None, None, sample_chargepoint_state(),
                     id="kein Timestamp gesetzt, kein Fehler aufgetreten"),
        pytest.param(sample(), 1652683242, None, None, sample_chargepoint_state(),
                     id="Timestamp gesetzt, kein Fehler aufgetreten"),
        pytest.param(sample_wrong_charge_state(), None, None, 1652683252,
                     sample_wrong_charge_state_chargepoint_state(), id="kein Timestamp gesetzt, Fehler aufgetreten"),
        pytest.param(sample_wrong_charge_state(), 1652683242, None, 1652683242,
                     sample_wrong_charge_state_chargepoint_state(),
                     id="Timestamp gesetzt, Fehler aufgetreten, Timestamp nicht abgelaufen"),
        pytest.param(sample_wrong_charge_state(), 1652683182, ValueError, 1652683182,
                     sample_chargepoint_state_resetted(),
                     id="Timestamp gesetzt, Fehler aufgetreten, Timestamp abgelaufen"),
    ])
def test_error_timestamp(sample_state,
                         error_timestamp,
                         expected_exception,
                         expected_error_timestamp,
                         expected_chargepoint_state,
                         monkeypatch,
                         requests_mock: requests_mock.mock):
    # setup
    mock_chargepoint_value_store = Mock()
    monkeypatch.setattr(chargepoint_module, 'get_chargepoint_value_store',
                        Mock(return_value=mock_chargepoint_value_store))
    requests_mock.post(f'http://{SAMPLE_IP}/connect.php')
    requests_mock.get(f'http://{SAMPLE_IP}/connect.php', json=sample_state)

    cp = chargepoint_module.ChargepointModule(OpenWBPro(configuration=OpenWBProConfiguration(ip_address=SAMPLE_IP)))
    cp.client_error_context.error_timestamp = error_timestamp
    cp.old_chargepoint_state = sample_chargepoint_state

    # evaluation
    if expected_exception is not None:
        cp.get_values()
        assert cp.fault_state.fault_state == FaultStateLevel.ERROR
        assert mock_chargepoint_value_store.call_count == 0
    else:
        cp.get_values()
        if expected_chargepoint_state is not None:
            assert vars(mock_chargepoint_value_store.set.call_args[0][0]) == vars(expected_chargepoint_state)
        else:
            assert mock_chargepoint_value_store.set.call_count == 0
    assert cp.client_error_context.error_timestamp == expected_error_timestamp
