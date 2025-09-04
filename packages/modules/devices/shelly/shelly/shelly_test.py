from unittest.mock import Mock
import requests_mock

from dataclasses import dataclass
from typing import Optional
import pytest

from modules.common.component_state import CounterState
from modules.conftest import SAMPLE_IP
from modules.devices.shelly.shelly.config import ShellyCounterSetup
from modules.devices.shelly.shelly import counter

# Shelly PLUG G1
DATA_PLUG_G1 = {
    "meters": [{
        "power": 230,
        "overpower": 0.00,
        "is_valid": True,
        "timestamp": 1756902511,
        "counters": [400.467, 1127.491, 1046.330],
        "total": 3981113
    }]
}
# Shelly EM 3 G1
DATA_EM_3_G1 = {
    # [...]
    "emeters": [{
        "power": 2300.00,
        "pf": 1.00,
        "current": 10.00,
        "voltage": 220.00,
        "is_valid": True,
        "total": 3000000.0,
        "total_returned": 0.0
    }, {
        "power": 460.00,
        "pf": 1.00,
        "current": 2.00,
        "voltage": 230.00,
        "is_valid": True,
        "total": 1000000.0,
        "total_returned": 0.0
    }, {
        "power": 230.00,
        "pf": 1.00,
        "current": 1.00,
        "voltage": 240.00,
        "is_valid": True,
        "total": 400000.0,
        "total_returned": 0.0
    }],
    "total_power": 2990.00,
    # [...]
}
# Shelly Pro 3EM G2
DATA_PRO_3EM_G2 = {
    "em:0": {
        "id": 0,
        "a_current": 1.0,
        "a_voltage": 220.0,
        "a_act_power": 230.0,
        "a_aprt_power": 71.2,
        "a_pf": 0.50,
        "a_freq": 50.0,
        "b_current": 2.0,
        "b_voltage": 230.0,
        "b_act_power": 460.0,
        "b_aprt_power": 58.8,
        "b_pf": 1.00,
        "b_freq": 50.0,
        "c_current": 10.0,
        "c_voltage": 240.0,
        "c_act_power": 2300.0,
        "c_aprt_power": 56.5,
        "c_pf": 1.50,
        "c_freq": 50.0,
        "n_current": "null",
        "total_current": 0.812,
        "total_act_power": 2990.00,
        "total_aprt_power": 186.512,
        "user_calibrated_phase": []
    },
    "emdata:0": {
        "id": 0,
        "a_total_act_energy": 24169.51,
        "a_total_act_ret_energy": 1356754.52,
        "b_total_act_energy": 19485.50,
        "b_total_act_ret_energy": 1256348.10,
        "c_total_act_energy": 18670.00,
        "c_total_act_ret_energy": 1211805.10,
        "total_act": 62325.00,
        "total_act_ret": 3824907.72
    },
}
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
            "by_minute": [0, 0, 0],
            "minute_ts": 1727857620
        },
        "ret_aenergy": {
            "total": 0,
            "by_minute": [0, 0, 0],
            "minute_ts": 1727857620
        }
    },
    # [..]
}
# Shelly 1PM G4
DATA_1PM_G4 = {
    # [...]
    "switch:0": {
        "id": 0,
        "source": "init",
        "output": True,
        "apower": 117.9,
        "voltage": 227.3,
        "freq": 52.0,
        "current": 0.65,
        "aenergy": {"total": 185774.593, "by_minute": [2394.379, 1795.784, 1995.316], "minute_ts": 1756903980},
        "ret_aenergy": {"total": 185618.039, "by_minute": [2394.379, 1795.784, 1995.316], "minute_ts": 1756903980},
        "temperature": {"tC": 54.8, "tF": 130.6}
    },
    # [...]
}


@dataclass
class CounterParams:
    name: str
    json_data: str
    factor: int = 1
    phase: int = 1
    generation: int = 1
    expected_counter_state: Optional[CounterState] = None


cases = [
    CounterParams(name="G1 - Shelly Plug Counter - Phase 1",
                  json_data=DATA_PLUG_G1, factor=1, phase=1, generation=1,
                  expected_counter_state=CounterState(
                      voltages=[230, 0, 0], power=230, currents=[1, 0, 0],
                      frequency=50, imported=100, exported=200, powers=[230, 0, 0])),
    CounterParams(name="G1 - Shelly Plug Counter - Phase 2",
                  json_data=DATA_PLUG_G1, factor=1, phase=2, generation=1,
                  expected_counter_state=CounterState(
                      voltages=[0, 230, 0], power=230, currents=[0, 1, 0],
                      frequency=50, imported=100, exported=200, powers=[0, 230, 0])),
    CounterParams(name="G1 - Shelly Plug Counter - Phase 3, Faktor -1",
                  json_data=DATA_PLUG_G1, factor=-1, phase=3, generation=1,
                  expected_counter_state=CounterState(
                      voltages=[0, 0, 230], power=-230, currents=[0, 0, -1],
                      frequency=50, imported=100, exported=200, powers=[0, 0, -230])),
    CounterParams(name="G1 - Shelly EM3 Counter - Phase 1, Faktor -1",
                  json_data=DATA_EM_3_G1, factor=1, phase=1, generation=1,
                  expected_counter_state=CounterState(
                      voltages=[220.0, 230.0, 240.0], power=2990.00, currents=[10.0, 2.0, 1.0], frequency=50,
                      imported=100, exported=200, powers=[2300, 460, 230], power_factors=[1.0, 1.0, 1.0])),
    CounterParams(name="G1 - Shelly EM3 Counter - Phase 2",
                  json_data=DATA_EM_3_G1, factor=-1, phase=2, generation=1,
                  expected_counter_state=CounterState(
                      voltages=[240.0, 220.0, 230.0], power=-2990.00, currents=[-1.0, -10.0, -2.0], frequency=50,
                      imported=100, exported=200, powers=[-230, -2300, -460], power_factors=[1.0, 1.0, 1.0])),
    CounterParams(name="G1 - Shelly EM3 Counter - Phase 3",
                  json_data=DATA_EM_3_G1, factor=1, phase=3, generation=1,
                  expected_counter_state=CounterState(
                      voltages=[230.0, 240.0, 220.0], power=2990.00, currents=[2.0, 1.0, 10.0], frequency=50,
                      imported=100, exported=200, powers=[460, 230, 2300], power_factors=[1.0, 1.0, 1.0])),
    CounterParams(name="G2 - Shelly Pro3 EM Counter - Phase 1",
                  json_data=DATA_PRO_3EM_G2, factor=1, phase=1, generation=2,
                  expected_counter_state=CounterState(
                      voltages=[220.0, 230.0, 240.0], power=2990.00, currents=[1.0, 2.0, 10.0], frequency=50,
                      imported=100, exported=200, powers=[230, 460, 2300], power_factors=[0.5, 1.0, 1.5])),
    CounterParams(name="G2 - Shelly Pro3 EM Counter - Phase 2, Faktor -1",
                  json_data=DATA_PRO_3EM_G2, factor=-1, phase=2, generation=2,
                  expected_counter_state=CounterState(
                      voltages=[240.0, 220.0, 230.0], power=-2990.00, currents=[-10.0, -1.0, -2.0], frequency=50,
                      imported=100, exported=200, powers=[-2300, -230, -460], power_factors=[1.5, 0.5, 1.0])),
    CounterParams(name="G2 - Shelly Pro3 EM Counter - Phase 3",
                  json_data=DATA_PRO_3EM_G2, factor=1, phase=3, generation=2,
                  expected_counter_state=CounterState(
                      voltages=[230.0, 240.0, 220.0], power=2990.00, currents=[2.0, 10.0, 1.0], frequency=50,
                      imported=100, exported=200, powers=[460, 2300, 230], power_factors=[1.0, 1.5, 0.5])),
    CounterParams(name="G3 - Shelly Mini PM Counter - Phase 1",
                  json_data=DATA_MINPM_G3, factor=1, phase=1, generation=3,
                  expected_counter_state=CounterState(
                      voltages=[230.9, 0, 0], power=230, currents=[1, 0, 0], frequency=51,
                      imported=100, exported=200, powers=[230, 0, 0])),
    CounterParams(name="G3 - Shelly Mini PM Counter - Phase 2",
                  json_data=DATA_MINPM_G3, factor=1, phase=2, generation=3,
                  expected_counter_state=CounterState(
                      voltages=[0, 230.9, 0], power=230, currents=[0, 1, 0], frequency=51,
                      imported=100, exported=200, powers=[0, 230, 0])),
    CounterParams(name="G3 - Shelly Mini PM Counter - Phase 3",
                  json_data=DATA_MINPM_G3, factor=1, phase=3, generation=3,
                  expected_counter_state=CounterState(
                      voltages=[0, 0, 230.9], power=230, currents=[0, 0, 1], frequency=51,
                      imported=100, exported=200, powers=[0, 0, 230])),
    CounterParams(name="G4 - Shelly 1PM Counter - Phase 1",
                  json_data=DATA_1PM_G4, factor=1, phase=1, generation=4,
                  expected_counter_state=CounterState(
                      voltages=[227.3, 0, 0], power=117.9, currents=[0.65, 0, 0], frequency=52,
                      imported=100, exported=200, powers=[117.9, 0, 0])),
    CounterParams(name="G4 - Shelly 1PM Counter - Phase 2",
                  json_data=DATA_1PM_G4, factor=1, phase=2, generation=4,
                  expected_counter_state=CounterState(
                      voltages=[0, 227.3, 0], power=117.9, currents=[0, 0.65, 0], frequency=52,
                      imported=100, exported=200, powers=[0, 117.9, 0])),
    CounterParams(name="G4 - Shelly 1PM Counter - Phase 3",
                  json_data=DATA_1PM_G4, factor=1, phase=3, generation=4,
                  expected_counter_state=CounterState(
                      voltages=[0, 0, 227.3], power=117.9, currents=[0, 0, 0.65], frequency=52,
                      imported=100, exported=200, powers=[0, 0, 117.9])),
]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_counter(params: CounterParams, monkeypatch, requests_mock: requests_mock.mock):
    mock_counter_value_store = Mock()
    monkeypatch.setattr(counter, "get_counter_value_store", Mock(return_value=mock_counter_value_store))
    if params.generation == 1:
        requests_mock.get(f"http://{SAMPLE_IP}/status", json=params.json_data)
    else:
        requests_mock.get(f"http://{SAMPLE_IP}/rpc/Shelly.GetStatus", json=params.json_data)
    mock_counter_value_store = Mock()
    monkeypatch.setattr(counter, "get_counter_value_store", Mock(return_value=mock_counter_value_store))
    c = counter.ShellyCounter(
        ShellyCounterSetup(), device_id=0, ip_address=SAMPLE_IP,
        factor=params.factor, phase=params.phase, generation=params.generation)
    c.initialize()

    # execution
    c.update()

    # evaluation
    assert vars(mock_counter_value_store.set.call_args[0][0]) == vars(params.expected_counter_state)
