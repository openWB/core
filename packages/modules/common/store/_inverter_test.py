from modules.common.store._inverter import PurgeInverterState
from modules.common.component_state import InverterState
from control.counter_all import CounterAll
from control.bat import Bat, BatData, Get
from typing import List, NamedTuple
from unittest.mock import Mock

import pytest


from control import data


@pytest.fixture(autouse=True)
def mock_data() -> None:
    data.data_init(Mock())
    data.data.counter_all_data = CounterAll()
    data.data.counter_all_data.data.get.hierarchy = []


STANDARD_HIERARCHY = [{"id": 0, "type": "counter",
                       "children": [{"id": 3, "type": "cp", "children": []}]},
                      {"id": 1, "type": "inverter", "children": []},
                      {"id": 2, "type": "bat", "children": []}]


HYBRID_HIERARCHY = [{"id": 0, "type": "counter",
                     "children": [{"id": 3, "type": "cp", "children": []}]},
                    {"id": 1, "type": "inverter",
                     "children": [{"id": 2, "type": "bat", "children": []}]}]


Params = NamedTuple("Params", [("name", str), ("hierarchy", List), ("expected_state", InverterState)])
cases = [
    Params("standard", STANDARD_HIERARCHY, InverterState(power=-5786, exported=200)),
    Params("hybrid", HYBRID_HIERARCHY, InverterState(power=-6009, exported=300))
]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_fix_hybrid_values(params):
    # setup
    data.data.counter_all_data.data.get.hierarchy = params.hierarchy
    data.data.bat_data["bat2"] = Mock(spec=Bat, data=Mock(
        spec=BatData, get=Mock(spec=Get, currents=[0]*3, power=223, exported=100, imported=200)))
    purge = PurgeInverterState(delegate=Mock(delegate=Mock(num=1)))

    # execution
    state = purge.fix_hybrid_values(InverterState(power=-5786, exported=200))

    # evaluation
    assert vars(state) == vars(params.expected_state)


FilterPeaksParams = NamedTuple("FilterPeaksParams", [(
    "name", str), ("max_ac_out", int), ("input_power", float), ("expected_power", float)])
filter_peaks_cases = [
    FilterPeaksParams("no_limit", 0, -5000, -5000),  # max_ac_out = 0 -> keine Begrenzung
    FilterPeaksParams("within_limit", 10000, -5000, -5000),  # innerhalb der Grenze
    FilterPeaksParams("exceeds_positive", 3000, 5000, 3000),  # überschreitet positive Grenze
    FilterPeaksParams("exceeds_negative", 3000, -5000, -3000),  # überschreitet negative Grenze (behält Vorzeichen)
    FilterPeaksParams("at_limit_positive", 5000, 5000, 5000),  # genau an der positiven Grenze
    FilterPeaksParams("at_limit_negative", 5000, -5000, -5000),  # genau an der negativen Grenze
]


@pytest.mark.parametrize("params", filter_peaks_cases, ids=[c.name for c in filter_peaks_cases])
def test_filter_peaks(params):
    # setup
    mock_inverter = Mock()
    mock_inverter.data.config.max_ac_out = params.max_ac_out
    data.data.pv_data = {"pv1": mock_inverter}

    purge = PurgeInverterState(delegate=Mock(delegate=Mock(num=1)))

    # execution
    input_state = InverterState(power=params.input_power, exported=1000)
    result_state = purge.filter_peaks(input_state)

    # evaluation
    assert result_state.power == params.expected_power
    assert result_state.exported == 1000  # exported sollte unverändert bleiben
