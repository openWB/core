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


@ pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
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
