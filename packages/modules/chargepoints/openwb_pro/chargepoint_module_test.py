from unittest.mock import Mock

import requests_mock


from modules.common.component_state import ChargepointState
from modules.chargepoints.openwb_pro import chargepoint_module

SAMPLE_IP = "1.1.1.1"


def test_openwb_pro(monkeypatch, requests_mock: requests_mock.mock):
    # setup
    mock_chargepoint_value_store = Mock()
    monkeypatch.setattr(chargepoint_module, 'get_chargepoint_value_store',
                        Mock(return_value=mock_chargepoint_value_store))
    requests_mock.post(f'http://{SAMPLE_IP}/connect.php')
    requests_mock.get(f'http://{SAMPLE_IP}/connect.php', json=SAMPLE)

    cp = chargepoint_module.ChargepointModule(0, {
        "type": "openwb_pro",
        "name": "openWB Pro",
        "configuration": {
                "ip_address": SAMPLE_IP
        }
    }, {})

    # execution
    cp.get_values()

    # evaluation
    assert vars(mock_chargepoint_value_store.set.call_args[0][0]) == vars(SAMPLE_CHARGEPOINT_STATE)


SAMPLE_CHARGEPOINT_STATE = ChargepointState(
    power=4302.7,
    currents=[6.133, 6.066, 6.122],
    imported=10839,
    exported=0,
    plug_state=True,
    charge_state=True,
    phases_in_use=3,
    rfid="98:ED:5C:B4:EE:8D"
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
          'vehicle_id': '98:ED:5C:B4:EE:8D'}
