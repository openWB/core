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
    requests_mock.get(f'http://{SAMPLE_IP}/api2.php', json=SAMPLE)

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
    power=13359,
    currents=[19.415, 19.545, 19.486],
    imported=8376,
    exported=3,
    plug_state=True,
    charge_state=True,
    phases_in_use=3
)

SAMPLE = {
    "date": "2021:12:08-17:59:51",
    "timestamp": 1638986391,
    "powers": [
        4422.3,
        4500.8,
        4436
    ],
    "power_all": 13359,
    "currents": [
        19.415,
        19.545,
        19.486
    ],
    "imported": 8376,
    "exported": 3,
    "plug_state": True,
    "charge_state": True,
    "phases_actual": 3,
    "phases_target": 3,
    "phases_in_use": 3,
    "offered_current": 32,
    "evse_signaling": "basic iec61851",
    "serial": "387107"
}
