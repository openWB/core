from unittest.mock import Mock

import requests_mock

from modules.common.component_state import CounterState
from modules.conftest import SAMPLE_IP
from modules.devices.vzlogger.vzlogger import counter
from modules.devices.vzlogger.vzlogger.config import (VZLogger, VZLoggerConfiguration, VZLoggerCounterConfiguration,
                                                      VZLoggerCounterSetup)
from modules.devices.vzlogger.vzlogger.device import create_device


def test_vzlogger_counter_update(monkeypatch, requests_mock: requests_mock.mock):
    # setup
    mock_counter_value_store = Mock()
    monkeypatch.setattr(counter, "get_counter_value_store", Mock(return_value=mock_counter_value_store))
    requests_mock.get(f"http://{SAMPLE_IP}", json=SAMPLE)
    device = create_device(VZLogger(configuration=VZLoggerConfiguration(ip_address=f"http://{SAMPLE_IP}")))
    device.add_component(VZLoggerCounterSetup(
        configuration=VZLoggerCounterConfiguration(line_exported=25, line_imported=37, line_power=13)))

    # execution
    device.update()

    # evaluation
    assert vars(mock_counter_value_store.set.call_args[0][0]) == vars(SAMPLE_COUNTER_STATE)


SAMPLE_COUNTER_STATE = CounterState(power=-500.0, imported=20000.0, exported=10000.0)
SAMPLE = {
    "version": "0.8.0",
    "generator": "vzlogger",
    "data": [
        {
            "uuid": "abc",
            "last": 1234,
            "interval": -1,
            "protocol": "sml",
            "tuples": [
                    [
                        1234,
                        -500
                    ]
            ]
        },
        {
            "uuid": "def",
            "last": 1234,
            "interval": -1,
            "protocol": "sml",
            "tuples": [
                    [
                        1234,
                        10000
                    ]
            ]
        },
        {
            "uuid": "ghi",
            "last": 1234,
            "interval": -1,
            "protocol": "sml",
            "tuples": [
                    [
                        1234,
                        20000
                    ]
            ]
        },
    ]
}
