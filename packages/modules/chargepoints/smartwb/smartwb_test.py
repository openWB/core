from typing import Dict
from unittest.mock import Mock

import pytest
import requests_mock
from modules.chargepoints.smartwb.config import SmartWB, SmartWBConfiguration


from modules.common.component_state import ChargepointState
from modules.chargepoints.smartwb import chargepoint_module


class Params:
    def __init__(self,
                 name: str,
                 sample_data: Dict,
                 sample_state: ChargepointState):
        self.name = name
        self.sample_data = sample_data
        self.sample_state = sample_state


class TestSmartWb:
    SAMPLE_CP_STATE_V1 = ChargepointState(
        power=5790,
        currents=[8.54, 8.54, 8.54],
        imported=54350.0,
        plug_state=True,
        charge_state=False,
        phases_in_use=3,
        serial_number="94:B9:7E:69:F0:D1"
    )
    SAMPLE_V1 = {
        "type": "parameters",
        "list": [{
            "vehicleState": 2,
            "evseState": False,
            "maxCurrent": 32,
            "actualCurrent": 32,
            "actualPower": 5.79,
            "duration": 1821561,
            "alwaysActive": False,
            "lastActionUser": "GUI",
            "lastActionUID": "GUI",
            "energy": 9.52,
            "mileage": 82.3,
            "meterReading": 54.35,
            "currentP1": 8.54,
            "currentP2": 8.54,
            "currentP3": 8.54
        }]
    }
    SAMPLE_CP_STATE_V2 = ChargepointState(
        phases_in_use=1,
        power=2251.0,
        powers=[2232.5784, 0, 0],
        currents=[9.78, 0, 0],
        voltages=[228.28, 231.85, 232.07],
        imported=54350.0,
        plug_state=True,
        charge_state=True,
        rfid="0a1b2c3d",
        rfid_timestamp=1652683252,
        serial_number="94:B9:7E:69:F0:D1"
    )
    SAMPLE_V2 = {
        "type": "parameters",
        "list": [
            {
                "vehicleState": 3,
                "evseState": False,
                "maxCurrent": 16,
                "actualCurrent": 10,
                "actualCurrentMA": 1000,
                "actualPower": 2.251,
                "duration": 1821000,
                "alwaysActive": False,
                "lastActionUser": "GUI",
                "lastActionUID": "GUI",
                "energy": 9.52,
                "mileage": 82.3,
                "meterReading": 54.35,
                "currentP1": 9.78,
                "currentP2": 0,
                "currentP3": 0,
                "voltageP1": 228.28,
                "voltageP2": 231.85,
                "voltageP3": 232.07,
                "useMeter": True,
                "RFIDUID": "0a1b2c3d"
            }]
    }
    SAMPLE_CP_STATE_NOT_CHARGING_V2 = ChargepointState(
        power=2251,
        currents=[0, 0, 0],
        voltages=[228.28, 231.85, 232.07],
        imported=54350.0,
        plug_state=True,
        charge_state=True,
        rfid="0a1b2c3d",
        rfid_timestamp=1652683252,
        phases_in_use=1,
        serial_number="94:B9:7E:69:F0:D1"
    )
    SAMPLE_NOT_CHARGING_V2 = {
        "type": "parameters",
        "list": [
            {
                "vehicleState": 3,
                "evseState": False,
                "maxCurrent": 16,
                "actualCurrent": 10,
                "actualCurrentMA": 1000,
                "actualPower": 2.251,
                "duration": 1821000,
                "alwaysActive": False,
                "lastActionUser": "GUI",
                "lastActionUID": "GUI",
                "energy": 9.52,
                "mileage": 82.3,
                "meterReading": 54.35,
                "currentP1": 0,
                "currentP2": 0,
                "currentP3": 0,
                "voltageP1": 228.28,
                "voltageP2": 231.85,
                "voltageP3": 232.07,
                "useMeter": True,
                "RFIDUID": "0a1b2c3d"
            }]
    }
    SAMPLE_HOST_DATA = {
        "type": "evseHost",
        "list": [
            {
                "ssid": "EVSE-WiFi",
                "dns": "192.168.4.1",
                "mac": "94:B9:7E:69:F0:D1",
                "ip": "192.168.4.1",
                "netmask": "255.255.255.0",
                "gateway": "0.0.0.0",
                "uptime": 1960,
                "opMode": "normal",
                "firmware": "2.2.5"
            }
        ]
    }

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        self.mock_chargepoint_value_store = Mock()
        monkeypatch.setattr(chargepoint_module, 'get_chargepoint_value_store',
                            Mock(return_value=self.mock_chargepoint_value_store))

    @pytest.fixture
    def cp(self) -> chargepoint_module.ChargepointModule:
        return chargepoint_module.ChargepointModule(SmartWB(configuration=SmartWBConfiguration(ip_address="1.1.1.1")))

    cases = [
        Params("smartWB V1", SAMPLE_V1, SAMPLE_CP_STATE_V1),
        Params("smartWB V2", SAMPLE_V2, SAMPLE_CP_STATE_V2),
        Params("smartWB V2 not charging", SAMPLE_NOT_CHARGING_V2, SAMPLE_CP_STATE_NOT_CHARGING_V2),
    ]

    @pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
    def test_get_values_v2(self, cp, requests_mock: requests_mock.mock, params: Params):
        # setup
        requests_mock.get("http://1.1.1.1/getParameters", json=params.sample_data)
        requests_mock.get("http://1.1.1.1/evseHost", json=self.SAMPLE_HOST_DATA)

        # execution
        cp.get_values()

        # evaluation
        assert self.mock_chargepoint_value_store.set.call_count == 1
        assert vars(self.mock_chargepoint_value_store.set.call_args[0][0]) == vars(params.sample_state)

    def test_set_current(self, cp, requests_mock: requests_mock.Mocker):
        # setup
        requests_mock.get('http://1.1.1.1/setCurrent')

        # execution
        cp.set_current(14.55)

        # evaluation
        assert requests_mock.request_history[0].query == "current=1455"
