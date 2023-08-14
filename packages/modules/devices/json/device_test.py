from unittest.mock import Mock

import pytest
import requests_mock

from modules.common.fault_state import FaultState
from modules.devices.json import bat, counter, inverter
from modules.devices.json.config import Json, JsonConfiguration, JsonBatSetup, JsonBatConfiguration, \
    JsonInverterConfiguration, JsonInverterSetup, JsonCounterSetup, JsonCounterConfiguration
from modules.devices.json.device import create_device


@pytest.fixture
def mock_value_store(monkeypatch):
    mock_value_store = Mock()
    mock_value_store_factory = Mock(return_value=mock_value_store)
    monkeypatch.setattr(bat, "get_bat_value_store", mock_value_store_factory)
    monkeypatch.setattr(counter, "get_counter_value_store", mock_value_store_factory)
    monkeypatch.setattr(inverter, "get_inverter_value_store", mock_value_store_factory)
    return mock_value_store


@pytest.mark.parametrize("component_config,expected_power", [
    pytest.param(JsonBatSetup(configuration=JsonBatConfiguration(jq_power=".some_value")), 42.0, id="bat"),
    pytest.param(JsonCounterSetup(configuration=JsonCounterConfiguration(jq_power=".some_value")), 42.0, id="counter"),
    pytest.param(JsonInverterSetup(configuration=JsonInverterConfiguration(jq_power=".some_value")), -42.0, id="pv"),
])
def test_device(monkeypatch, mock_value_store: Mock, requests_mock: requests_mock.Mocker, component_config,
                expected_power: float):
    # setup
    monkeypatch.setattr(FaultState, "store_error", Mock())
    requests_mock.get("http://sample_host/sample_path", json={"some_value": 42})
    device_config = Json(configuration=JsonConfiguration("http://sample_host/sample_path"))

    # execution
    device = create_device(device_config)
    device.add_component(component_config)
    device.update()

    # evaluation
    assert len(mock_value_store.set.mock_calls) == 1
    assert mock_value_store.set.call_args[0][0].power == expected_power


def test_counter_powers(monkeypatch, mock_value_store: Mock, requests_mock: requests_mock.Mocker):
    # setup
    monkeypatch.setattr(FaultState, "store_error", Mock())
    requests_mock.get("http://sample_host/sample_path",
                      json={"power": 42, "power_l1": 11, "power_l2": 12, "power_l3": 13})
    device_config = Json(configuration=JsonConfiguration("http://sample_host/sample_path"))

    # execution
    device = create_device(device_config)
    device.add_component(JsonCounterSetup(configuration=JsonCounterConfiguration(jq_power=".power",
                                                                                 jq_power_l1=".power_l1",
                                                                                 jq_power_l2=".power_l2",
                                                                                 jq_power_l3=".power_l3")))
    device.update()

    # evaluation
    assert len(mock_value_store.set.mock_calls) == 1
    assert mock_value_store.set.call_args[0][0].power == 42
    assert mock_value_store.set.call_args[0][0].powers == [11, 12, 13]


def test_counter_currents(monkeypatch, mock_value_store: Mock, requests_mock: requests_mock.Mocker):
    # setup
    monkeypatch.setattr(FaultState, "store_error", Mock())
    requests_mock.get("http://sample_host/sample_path",
                      json={"power": 42, "current_l1": 11, "current_l2": 12, "current_l3": 13})
    device_config = Json(configuration=JsonConfiguration("http://sample_host/sample_path"))

    # execution
    device = create_device(device_config)
    device.add_component(JsonCounterSetup(configuration=JsonCounterConfiguration(jq_power=".power",
                                                                                 jq_current_l1=".current_l1",
                                                                                 jq_current_l2=".current_l2",
                                                                                 jq_current_l3=".current_l3")))
    device.update()

    # evaluation
    assert len(mock_value_store.set.mock_calls) == 1
    assert mock_value_store.set.call_args[0][0].power == 42
    assert mock_value_store.set.call_args[0][0].currents == [11, 12, 13]
