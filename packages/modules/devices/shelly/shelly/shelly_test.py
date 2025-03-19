from unittest.mock import Mock
import requests_mock

from modules.common.component_state import CounterState
from modules.conftest import SAMPLE_IP
from modules.devices.shelly.shelly.config import ShellyCounterSetup
from modules.devices.shelly.shelly import counter


# Shelly MiniPM G3 https://forum.openwb.de/viewtopic.php?p=117309#p117309
DATA_MINPM_G3 = {
    # [..]
    "pm1:0": {
        "id": 0,
        "voltage": 230.9,
        "current": 1,
        "apower": 230,
        "freq": 51,
        "aenergy": {
            "total": 3195.88,
            "by_minute": [
                0,
                0,
                0
            ],
            "minute_ts": 1727857620
        },
        "ret_aenergy": {
            "total": 0,
            "by_minute": [
                0,
                0,
                0
            ],
            "minute_ts": 1727857620
        }
    },
    # [..]
}


def test_counter_shelly_minipm_g3(monkeypatch, requests_mock: requests_mock.mock):
    mock_counter_value_store = Mock()
    monkeypatch.setattr(counter, "get_counter_value_store", Mock(return_value=mock_counter_value_store))
    requests_mock.get(f"http://{SAMPLE_IP}/rpc/Shelly.GetStatus", json=DATA_MINPM_G3)
    mock_counter_value_store = Mock()
    monkeypatch.setattr(counter, "get_counter_value_store", Mock(return_value=mock_counter_value_store))
    c = counter.ShellyCounter(0, ShellyCounterSetup(), SAMPLE_IP, 1, 2)

    # execution
    c.update()

    # evaluation
    assert vars(mock_counter_value_store.set.call_args[0][0]) == vars(SAMPLE_COUNTER_STATE)


SAMPLE_COUNTER_STATE = CounterState(voltages=[230.9, 0, 0], power=230, currents=[
                                    1, 0, 0], frequency=51, imported=100, exported=200)
