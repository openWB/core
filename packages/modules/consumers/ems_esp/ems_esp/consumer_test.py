from unittest.mock import Mock

import pytest
import requests_mock

from modules.common import configurable_consumer
from modules.consumers.ems_esp.ems_esp.config import EmsEsp, EmsEspConfiguration
from modules.consumers.ems_esp.ems_esp.consumer import create_consumer

SAMPLE_IP = "1.1.1.1"


def _create_consumer(monkeypatch):
    # ConfigurableConsumer.__init__ needs a store, uninteresting for these tests
    monkeypatch.setattr(configurable_consumer, "get_component_value_store", Mock())
    config = EmsEsp(configuration=EmsEspConfiguration(ip_address=SAMPLE_IP, token="testtoken"))
    return create_consumer(config)


def test_update_uses_heatpump_entity_when_available(monkeypatch, requests_mock: requests_mock.Mocker):
    requests_mock.get(f"http://{SAMPLE_IP}/api/heatpump", json={"hpcurrpower": 42})
    consumer = _create_consumer(monkeypatch)

    state = consumer.module_updater()

    assert state.power == 42
    # 2 calls on this first cycle: the detection probe, then update()'s own fetch for the real
    # reading - no /api/boiler request at all, since detection never needed to fall back to it
    assert requests_mock.call_count == 2
    assert all(c.url.endswith("/api/heatpump") for c in requests_mock.request_history)


def test_update_falls_back_to_boiler_when_heatpump_device_unknown(monkeypatch, requests_mock: requests_mock.Mocker):
    # matches issue #4282: Bosch Compress 6800i has no "heatpump" device, its hp* entities
    # (incl. hpcurrpower) live under "boiler" instead
    requests_mock.get(f"http://{SAMPLE_IP}/api/heatpump", status_code=404,
                      json={"message": "unknown device heatpump"})
    requests_mock.get(f"http://{SAMPLE_IP}/api/boiler", json={"hpcurrpower": 28, "curflowtemp": 46.5})
    consumer = _create_consumer(monkeypatch)

    state = consumer.module_updater()

    assert state.power == 28


def test_detected_base_url_is_cached_across_calls(monkeypatch, requests_mock: requests_mock.Mocker):
    requests_mock.get(f"http://{SAMPLE_IP}/api/heatpump", status_code=404)
    requests_mock.get(f"http://{SAMPLE_IP}/api/boiler", json={"hpcurrpower": 10})
    consumer = _create_consumer(monkeypatch)

    consumer.module_updater()
    consumer.module_updater()

    heatpump_calls = [c for c in requests_mock.request_history if c.url.endswith("/api/heatpump")]
    assert len(heatpump_calls) == 1


def test_switch_on_uses_detected_base_url(monkeypatch, requests_mock: requests_mock.Mocker):
    requests_mock.get(f"http://{SAMPLE_IP}/api/heatpump", status_code=404)
    requests_mock.get(f"http://{SAMPLE_IP}/api/boiler", json={"hpcurrpower": 10})
    post_mock = requests_mock.post(f"http://{SAMPLE_IP}/api/boiler/hpin4opt", json={})
    consumer = _create_consumer(monkeypatch)

    consumer.module_switch_on()

    assert post_mock.called


def test_raises_when_neither_device_has_hpcurrpower(monkeypatch, requests_mock: requests_mock.Mocker):
    requests_mock.get(f"http://{SAMPLE_IP}/api/heatpump", json={"other": 1})
    requests_mock.get(f"http://{SAMPLE_IP}/api/boiler", json={"other": 2})
    consumer = _create_consumer(monkeypatch)

    with pytest.raises(ValueError):
        consumer.module_updater()
