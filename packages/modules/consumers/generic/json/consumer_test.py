from unittest.mock import Mock

import requests_mock

from modules.common import configurable_consumer
from modules.consumers.generic.json.config import Json, JsonConfiguration
from modules.consumers.generic.json.consumer import create_consumer

SAMPLE_URL = "http://1.1.1.1/status"


def _create_consumer(monkeypatch, **configuration_kwargs):
    # ConfigurableConsumer.__init__ needs a store, uninteresting for these tests
    monkeypatch.setattr(configurable_consumer, "get_component_value_store", Mock())
    config = Json(configuration=JsonConfiguration(
        url=SAMPLE_URL, jq_power=".power", **configuration_kwargs))
    return create_consumer(config)


def test_temperatures_is_none_when_jq_temperatures_not_configured(monkeypatch, requests_mock: requests_mock.Mocker):
    # discussion #3466, discussioncomment-19500817: without jq_temperatures, temperatures must stay
    # None, not [None] - setdata.py rejects a list containing None as an invalid payload
    requests_mock.get(SAMPLE_URL, json={"power": 123})
    consumer = _create_consumer(monkeypatch)

    state = consumer.module_updater()

    assert state.temperatures is None


def test_temperatures_is_wrapped_in_list_when_jq_temperatures_configured(
        monkeypatch, requests_mock: requests_mock.Mocker):
    requests_mock.get(SAMPLE_URL, json={"power": 123, "temp": 42.5})
    consumer = _create_consumer(monkeypatch, jq_temperatures=".temp")

    state = consumer.module_updater()

    assert state.temperatures == [42.5]
