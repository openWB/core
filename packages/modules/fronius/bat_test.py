import pytest

import requests_mock
from unittest.mock import Mock

from modules.common.simcount import SimCountLegacy
from modules.fronius import bat, device
from helpermodules import compatibility
from test_utils.mock_ramdisk import MockRamdisk


@pytest.fixture
def mock_ramdisk(monkeypatch):
    monkeypatch.setattr(compatibility, "is_ramdisk_in_use", lambda: True)
    return MockRamdisk(monkeypatch)


def test_update(monkeypatch, requests_mock: requests_mock.Mocker, mock_ramdisk):
    component_config = bat.get_default_config()
    device_config = device.get_default_config()["configuration"]
    assert device_config["meter_id"] == 0
    battery = bat.FroniusBat(0, component_config, device_config)

    monkeypatch.setattr(SimCountLegacy, "sim_count", Mock(return_value=[0, 0]))
    requests_mock.get(
        "http://" + device_config["ip_address"] + "/solar_api/v1/GetPowerFlowRealtimeData.fcgi",
        json=json)

    battery_state = battery.update()

    assert battery_state.exported == 0
    assert battery_state.imported == 0
    assert battery_state.power == -2288
    assert battery_state.soc == 60.8


json = {
    "Body": {
        "Data": {
            "Inverters": {
                "1": {
                    "Battery_Mode": "normal",
                    "DT": 1,
                    "E_Day": None,
                    "E_Total": 9805020.3608333338,
                    "E_Year": None,
                    "P": 2246.208984375,
                    "SOC": 60.799999999999997
                }
            },
            "Site": {
                "BackupMode": "false",
                "BatteryStandby": "true",
                "E_Day": None,
                "E_Total": 9805020.3608333338,
                "E_Year": None,
                "Meter_Location": "grid",
                "Mode": "bidirectional",
                "P_Akku": 2288.587158203125,
                "P_Grid": 280.39999999999998,
                "P_Load": -2938.6320312500002,
                "P_PV": 3.5314908027648926,
                "rel_Autonomy": 90.458145252002623,
                "rel_SelfConsumption": 100.0
            },
            "Smartloads": {
                "Ohmpilots": {}
            },
            "Version": "12"
        }
    },
    "Head": {
        "RequestArguments": {},
        "Status": {
            "Code": 0,
            "Reason": "",
            "UserMessage": ""
        },
        "Timestamp": "2022-01-03T17:17:36+00:00"
    }
}
