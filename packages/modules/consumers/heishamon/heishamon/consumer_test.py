import json
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from control.consumer.consumer_data import ConsumerUsage
from modules.common import configurable_consumer
from modules.consumers.heishamon.heishamon.config import HeishaMon, HeishaMonConfiguration
from modules.consumers.heishamon.heishamon.consumer import create_consumer, TEMPERATURE_NAMES
from modules.consumers.heishamon.vendor import vendor_descriptor

SAMPLE_URL = "http://heishamon.local/json"


@pytest.fixture
def response():
    # Relevant subset of the user's /json response; unrelated fields must not affect the result.
    return json.loads(Path(__file__).with_name("sample.json").read_text())


@pytest.fixture
def consumer(monkeypatch):
    monkeypatch.setattr(configurable_consumer, "get_component_value_store", Mock())
    return create_consumer(HeishaMon(configuration=HeishaMonConfiguration(ip_address="heishamon.local")))


def _set_value(response, name, value):
    next(entry for entry in response["heatpump"] if entry["Name"] == name)["Value"] = value


def test_user_response(consumer, response, requests_mock):
    requests_mock.get(SAMPLE_URL, json=response)

    state = consumer.module_updater()

    assert state.power == 1200
    assert state.temperatures == [40.5, 42.75, 48]
    assert state.imported is None  # The core integrates energy from power.
    assert requests_mock.call_count == 1
    assert requests_mock.last_request.method == "GET"
    assert requests_mock.last_request.timeout == 5


def test_only_requested_consumption_is_used(consumer, response, requests_mock):
    _set_value(response, "Heat_Power_Production", 9000)
    _set_value(response, "Cool_Power_Consumption", 300)
    _set_value(response, "DHW_Power_Consumption", 800)
    response["heatpump extra"] = [{"Name": "Heat_Power_Consumption_Extra", "Value": 2000}]
    requests_mock.get(SAMPLE_URL, json=response)

    assert consumer.module_updater().power == 1200


def test_topics_are_identified_by_name_not_position(consumer, response, requests_mock):
    response["heatpump"].reverse()
    response["heatpump"].extend([None, {}, {"Name": "Unknown", "Value": 123}])
    requests_mock.get(SAMPLE_URL, json=response)

    state = consumer.module_updater()

    assert state.power == 1200
    assert state.temperatures == [40.5, 42.75, 48]


@pytest.mark.parametrize("power", [0, "0", 1200, "1200", 1234.5, "1234.5"])
def test_numeric_power_and_real_zero(consumer, response, requests_mock, power):
    _set_value(response, "Heat_Power_Consumption", power)
    requests_mock.get(SAMPLE_URL, json=response)

    assert consumer.module_updater().power == float(power)


@pytest.mark.parametrize("power", [-200, "-200", None, "", "unknown", "NaN", "Infinity", [], {}, True])
def test_invalid_power_is_not_reported_as_zero(consumer, response, requests_mock, power):
    _set_value(response, "Heat_Power_Consumption", power)
    requests_mock.get(SAMPLE_URL, json=response)

    with pytest.raises(ValueError, match="Heat_Power_Consumption"):
        consumer.module_updater()


def test_missing_power_is_an_error(consumer, response, requests_mock):
    response["heatpump"] = [entry for entry in response["heatpump"] if entry["Name"] != "Heat_Power_Consumption"]
    requests_mock.get(SAMPLE_URL, json=response)

    with pytest.raises(ValueError, match="Heat_Power_Consumption"):
        consumer.module_updater()


@pytest.mark.parametrize("response", [None, [], {}, {"heatpump": None}, {"heatpump": {}}, {"heatpump": []}])
def test_missing_or_invalid_heatpump_data(consumer, response, requests_mock):
    requests_mock.get(SAMPLE_URL, text=json.dumps(response))

    with pytest.raises(ValueError):
        consumer.module_updater()


@pytest.mark.parametrize("name", TEMPERATURE_NAMES)
@pytest.mark.parametrize("temperature", [None, -128, -78, 101, "NaN", "bad", True])
def test_invalid_optional_temperature_preserves_slots(consumer, response, requests_mock, name, temperature):
    _set_value(response, name, temperature)
    requests_mock.get(SAMPLE_URL, json=response)

    state = consumer.module_updater()
    expected = [40.5, 42.75, 48]
    expected[TEMPERATURE_NAMES.index(name)] = None
    assert state.power == 1200
    assert state.temperatures == expected


def test_missing_optional_temperature_preserves_slots(consumer, response, requests_mock):
    response["heatpump"] = [entry for entry in response["heatpump"] if entry["Name"] != "Main_Outlet_Temp"]
    requests_mock.get(SAMPLE_URL, json=response)

    assert consumer.module_updater().temperatures == [40.5, None, 48]


def test_power_only_response(consumer, requests_mock):
    requests_mock.get(SAMPLE_URL, json={"heatpump": [{"Name": "Heat_Power_Consumption", "Value": 1200}]})

    state = consumer.module_updater()

    assert state.power == 1200
    assert state.temperatures == [None, None, None]


def test_temperatures_can_be_disabled(consumer, response, requests_mock):
    consumer.config.configuration.read_temperatures = False
    requests_mock.get(SAMPLE_URL, json=response)

    state = consumer.module_updater()

    assert state.power == 1200
    assert state.temperatures is None


def test_numeric_temperature_strings(consumer, response, requests_mock):
    for name in TEMPERATURE_NAMES:
        _set_value(response, name, "42.75")
    requests_mock.get(SAMPLE_URL, json=response)

    assert consumer.module_updater().temperatures == [42.75, 42.75, 42.75]


def test_values_are_refreshed_each_update(consumer, response, requests_mock):
    requests_mock.get(SAMPLE_URL, json=response)
    assert consumer.module_updater().power == 1200
    _set_value(response, "Heat_Power_Consumption", 600)
    requests_mock.get(SAMPLE_URL, json=response)

    assert consumer.module_updater().power == 600
    assert requests_mock.call_count == 2


@pytest.mark.parametrize("status", [401, 404, 500])
def test_http_errors_are_propagated(consumer, requests_mock, status):
    requests_mock.get(SAMPLE_URL, status_code=status)

    with pytest.raises(requests.exceptions.HTTPError):
        consumer.module_updater()


def test_timeout_is_propagated(consumer, requests_mock):
    requests_mock.get(SAMPLE_URL, exc=requests.exceptions.Timeout)

    with pytest.raises(requests.exceptions.Timeout):
        consumer.module_updater()


def test_invalid_json_is_propagated(consumer, requests_mock):
    requests_mock.get(SAMPLE_URL, text="<html>not JSON</html>")

    with pytest.raises(ValueError):
        consumer.module_updater()


def test_configuration_and_descriptor():
    config = HeishaMon()

    assert config.type == "heishamon"
    assert config.vendor == vendor_descriptor.configuration_factory().type
    assert config.usage == (ConsumerUsage.METER_ONLY,)
    assert config.configuration.read_temperatures is True
    assert config.configuration.ip_address is None
