from typing import Dict
from unittest.mock import Mock
import requests_mock

import pytest

from modules.chargepoints.openwb_pro.config import OpenWBPro, OpenWBProConfiguration
from modules.common.component_state import ChargepointState
from modules.chargepoints.openwb_pro import chargepoint_module
from modules.conftest import SAMPLE_IP

SAMPLE_CHARGEPOINT_STATE = ChargepointState(
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

SAMPLE = {'charge_state': True,
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

SAMPLE_CHARGEPOINT_STATE_EXTENDED = ChargepointState(
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

SAMPLE_EXTENDED = {"date": "2023:09:18-15:13:41",
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
                         [pytest.param(SAMPLE, SAMPLE_CHARGEPOINT_STATE),
                          pytest.param(SAMPLE_EXTENDED, SAMPLE_CHARGEPOINT_STATE_EXTENDED)
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
