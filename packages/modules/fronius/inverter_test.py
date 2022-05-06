import pytest

import requests_mock
from unittest.mock import Mock

from modules.common.simcount import SimCountLegacy
from modules.fronius import inverter, device
from helpermodules import compatibility
from test_utils.mock_ramdisk import MockRamdisk


@pytest.fixture
def mock_ramdisk(monkeypatch):
    monkeypatch.setattr(compatibility, "is_ramdisk_in_use", lambda: True)
    return MockRamdisk(monkeypatch)


def test_update(monkeypatch, requests_mock: requests_mock.Mocker, mock_ramdisk):
    component_config = inverter.get_default_config()
    assert component_config["configuration"]["ip_address2"] == "none"
    device_config = device.get_default_config()["configuration"]
    wr = inverter.FroniusInverter(0, component_config, device_config)

    monkeypatch.setattr(SimCountLegacy, "sim_count", Mock(return_value=[0, 0]))
    requests_mock.get(
        "http://" + device_config["ip_address"] + "/solar_api/v1/GetPowerFlowRealtimeData.fcgi",
        json=json_wr1)

    inverter_state = wr.update()

    assert inverter_state.counter == 0
    assert inverter_state.currents == [0, 0, 0]
    assert inverter_state.power == -196.08712768554688


def test_update_wr2(monkeypatch, requests_mock: requests_mock.Mocker, mock_ramdisk):
    component_config = inverter.get_default_config()
    component_config["configuration"]["ip_address2"] = "ip-address-wr2"
    device_config = device.get_default_config()["configuration"]
    wr = inverter.FroniusInverter(0, component_config, device_config)

    monkeypatch.setattr(SimCountLegacy, "sim_count", Mock(return_value=[0, 0]))
    requests_mock.get(
        "http://" + device_config["ip_address"] + "/solar_api/v1/GetPowerFlowRealtimeData.fcgi",
        json=json_wr1)
    requests_mock.get(
        "http://" + component_config["configuration"]["ip_address2"] + "/solar_api/v1/GetPowerFlowRealtimeData.fcgi",
        json=json_wr2)

    inverter_state = wr.update()

    assert inverter_state.counter == 0
    assert inverter_state.currents == [0, 0, 0]
    assert inverter_state.power == -304.08712768554688


json_wr1 = {
   "Body": {
      "Data": {
         "Inverters": {
            "1": {
               "Battery_Mode": "normal",
               "DT": 1,
               "E_Day": None,
               "E_Total": 9824871.8336111102,
               "E_Year": None,
               "P": 1263.8095703125,
               "SOC": 41.100000000000001
            }
         },
         "Site": {
            "BackupMode": "false",
            "BatteryStandby": "true",
            "E_Day": None,
            "E_Total": 9824871.8336111102,
            "E_Year": None,
            "Meter_Location": "grid",
            "Mode": "bidirectional",
            "P_Akku": 1126.365966796875,
            "P_Grid": -107.8,
            "P_Load": -1143.5296386718751,
            "P_PV": 196.08712768554688,
            "rel_Autonomy": 100.0,
            "rel_SelfConsumption": 91.385163695601761
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
      "Timestamp": "2022-01-04T09:45:59+00:00"
   }
}

json_wr2 = {
   "Body": {
      "Data": {
         "Inverters": {
            "1": {
               "DT": 232,
               "E_Day": 172.69999694824219,
               "E_Total": 3372.76953125,
               "E_Year": 10754989,
               "P": 108
            }
         },
         "Site": {
            "E_Day": 172.69999694824219,
            "E_Total": 3372.7694444444446,
            "E_Year": 10754989,
            "Meter_Location": "unknown",
            "Mode": "produce-only",
            "P_Akku": None,
            "P_Grid": None,
            "P_Load": None,
            "P_PV": 108,
            "rel_Autonomy": None,
            "rel_SelfConsumption": None
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
      "Timestamp": "2021-12-30T10:37:02+01:00"
   }
}
