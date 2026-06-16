from unittest.mock import Mock

import pytest
import requests_mock

from dataclass_utils import dataclass_from_dict
from helpermodules import compatibility
from modules.conftest import SAMPLE_IP
from modules.common.component_state import InverterState
from modules.devices.fronius.fronius import inverter_production_meter
from modules.devices.fronius.fronius.config import FroniusConfiguration, FroniusProductionMeterSetup
from test_utils.mock_ramdisk import MockRamdisk


@pytest.fixture
def mock_ramdisk(monkeypatch):
    monkeypatch.setattr(compatibility, "is_ramdisk_in_use", lambda: True)
    return MockRamdisk(monkeypatch)


def test_production_count(monkeypatch, requests_mock: requests_mock.mock):
    mock_inverter_value_store = Mock()
    monkeypatch.setattr(inverter_production_meter, "get_component_value_store",
                        Mock(return_value=mock_inverter_value_store))
    requests_mock.get(f"http://{SAMPLE_IP}/solar_api/v1/GetMeterRealtimeData.cgi", json=json_ext_var2)
    mock_inverter_value_store = Mock()
    monkeypatch.setattr(inverter_production_meter, "get_component_value_store",
                        Mock(return_value=mock_inverter_value_store))

    component_config = FroniusProductionMeterSetup()
    component_config.configuration.variant = 2
    device_config = FroniusConfiguration()
    device_config.ip_address = SAMPLE_IP
    component_config.configuration.meter_id = 1
    i = inverter_production_meter.FroniusProductionMeter(component_config, device_config=dataclass_from_dict(
        FroniusConfiguration, device_config), device_id=0)
    i.initialize()

    # execution
    i.update()

    # evaluation
    assert vars(mock_inverter_value_store.set.call_args[0][0]) == vars(SAMPLE_INVERTER_STATE)


SAMPLE_INVERTER_STATE = InverterState(power=3809.4,
                                      currents=[-5.373121093182142, -5.664436188811191, -5.585225225225224],
                                      exported=200)


json_ext_var2 = {
    "Body": {
        "Data": {
            "1": {
                "ACBRIDGE_CURRENT_ACTIVE_MEAN_01_F32": -8.4849999999999994,
                "ACBRIDGE_CURRENT_ACTIVE_MEAN_02_F32": -8.5009999999999994,
                "ACBRIDGE_CURRENT_ACTIVE_MEAN_03_F32": -8.5350000000000001,
                "ACBRIDGE_CURRENT_AC_SUM_NOW_F64": -25.520999999999997,
                "ACBRIDGE_VOLTAGE_MEAN_12_F32": 396.69999999999999,
                "ACBRIDGE_VOLTAGE_MEAN_23_F32": 396.80000000000001,
                "ACBRIDGE_VOLTAGE_MEAN_31_F32": 397.19999999999999,
                "COMPONENTS_MODE_ENABLE_U16": 1.0,
                "COMPONENTS_MODE_VISIBLE_U16": 1.0,
                "COMPONENTS_TIME_STAMP_U64": 1611650230.0,
                "Details": {
                    "Manufacturer": "Fronius",
                    "Model": "Smart Meter TS 65A-3",
                    "Serial": "1234567890"
                },
                "GRID_FREQUENCY_MEAN_F32": 49.899999999999999,
                "SMARTMETER_ENERGYACTIVE_ABSOLUT_MINUS_F64": 28233.0,
                "SMARTMETER_ENERGYACTIVE_ABSOLUT_PLUS_F64": 5094426.0,
                "SMARTMETER_ENERGYACTIVE_CONSUMED_SUM_F64": 28233.0,
                "SMARTMETER_ENERGYACTIVE_PRODUCED_SUM_F64": 5094426.0,
                "SMARTMETER_ENERGYREACTIVE_CONSUMED_SUM_F64": 5905771.0,
                "SMARTMETER_ENERGYREACTIVE_PRODUCED_SUM_F64": 31815.0,
                "SMARTMETER_FACTOR_POWER_01_F64": 0.64300000000000002,
                "SMARTMETER_FACTOR_POWER_02_F64": 0.68000000000000005,
                "SMARTMETER_FACTOR_POWER_03_F64": 0.66700000000000004,
                "SMARTMETER_FACTOR_POWER_SUM_F64": 0.66300000000000003,
                "SMARTMETER_POWERACTIVE_01_F64": 1229.7,
                "SMARTMETER_POWERACTIVE_02_F64": 1298.0999999999999,
                "SMARTMETER_POWERACTIVE_03_F64": 1281.5,
                "SMARTMETER_POWERACTIVE_MEAN_01_F64": -1232.0566666666653,
                "SMARTMETER_POWERACTIVE_MEAN_02_F64": -1296.0230000000006,
                "SMARTMETER_POWERACTIVE_MEAN_03_F64": -1281.2506666666663,
                "SMARTMETER_POWERACTIVE_MEAN_SUM_F64": 3809.4000000000001,
                "SMARTMETER_POWERAPPARENT_01_F64": 1911.8,
                "SMARTMETER_POWERAPPARENT_02_F64": 1910.0999999999999,
                "SMARTMETER_POWERAPPARENT_03_F64": 1922.3,
                "SMARTMETER_POWERAPPARENT_MEAN_01_F64": 1910.7656666666664,
                "SMARTMETER_POWERAPPARENT_MEAN_02_F64": 1904.090666666666,
                "SMARTMETER_POWERAPPARENT_MEAN_03_F64": 1923.9343333333331,
                "SMARTMETER_POWERAPPARENT_MEAN_SUM_F64": 5744.3000000000002,
                "SMARTMETER_POWERREACTIVE_01_F64": 1463.8,
                "SMARTMETER_POWERREACTIVE_02_F64": 1401.0999999999999,
                "SMARTMETER_POWERREACTIVE_03_F64": 1432.8,
                "SMARTMETER_POWERREACTIVE_MEAN_SUM_F64": 4297.8999999999996,
                "SMARTMETER_VALUE_LOCATION_U16": 3.0,
                "SMARTMETER_VOLTAGE_01_F64": 229.30000000000001,
                "SMARTMETER_VOLTAGE_02_F64": 228.80000000000001,
                "SMARTMETER_VOLTAGE_03_F64": 229.40000000000001,
                "SMARTMETER_VOLTAGE_MEAN_01_F64": 228.8716666666669,
                "SMARTMETER_VOLTAGE_MEAN_02_F64": 228.90133333333321,
                "SMARTMETER_VOLTAGE_MEAN_03_F64": 229.3593333333333
            }
        }
    },
    "Head": {
        "RequestArguments": {
            "DeviceClass": "Meter",
            "Scope": "System"
        },
        "Status": {
            "Code": 0,
            "Reason": "",
            "UserMessage": ""
        },
        "Timestamp": "2021-01-26T08:37:11+00:00"
    }
}
