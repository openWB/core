# bad integration test

from typing import Callable, NamedTuple
from unittest.mock import Mock

import pytest


from control import data
from control.bat import Bat
from control.chargepoint import Chargepoint
from control.counter import Counter, CounterAll
from control.pv import Pv
from modules.common.component_state import CounterState
from modules.common.store._counter import PurgeCounterState


@pytest.fixture(autouse=True)
def mock_data() -> None:
    data.data_init(Mock())
    data.data.counter_data["all"] = CounterAll()
    data.data.counter_data["all"].data.update({"get": {"hierarchy": []}})


def add_chargepoint(id: int):
    data.data.cp_data[f"cp{id}"] = Mock(spec=Chargepoint,
                                        id=id,
                                        chargepoint_module=Mock(),
                                        data=Mock(
                                            config=Mock(phase_1=1),
                                            get=Mock(power=13359,
                                                     currents=[19.36, 19.36, 19.36],
                                                     imported=0,
                                                     exported=0)))


def mock_data_standard():
    add_chargepoint(3)
    data.data.bat_data["inverter1"] = Mock(spec=Pv, data={"get": {"power": 5786, "exported": 200}})
    data.data.bat_data["bat2"] = Mock(spec=Bat, data={"get": {"power": 223, "exported": 200, "imported": 100}})
    data.data.counter_data["all"].data["get"]["hierarchy"] = [{"id": 0, "type": "counter",
                                                               "children": [{"id": 3, "type": "cp", "children": []}]},
                                                              {"id": 1, "type": "inverter", "children": []},
                                                              {"id": 2, "type": "bat", "children": []}]


def mock_data_nested():
    add_chargepoint(1)
    add_chargepoint(3)
    data.data.counter_data["counter2"] = Mock(
        spec=Counter, data={"get": {"power": 13359, "exported": 0, "imported": 0, "currents": [19.36, 19.36, 19.36]}})
    data.data.counter_data["all"].data["get"]["hierarchy"] = [
        {"id": 0, "type": "counter",
         "children": [{"id": 1, "type": "cp", "children": []},
                      {"id": 2, "type": "counter",
                       "children": [
                           {"id": 3, "type": "cp", "children": []}]}]}]


Params = NamedTuple("Params", [("name", str), ("mock_data", Callable), ("expected_state", CounterState)])
cases = [
    Params("standard", mock_data_standard, CounterState(power=8358, currents=[26.61]*3, exported=200, imported=100)),
    Params("nested virtual", mock_data_nested, CounterState(
        power=21717, currents=[45.97]*3, exported=200, imported=100))
]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_calc_virtual(params):
    # setup
    params.mock_data()
    purge = PurgeCounterState(delegate=Mock(delegate=Mock(num=0)), add_child_values=True)

    # execution
    state = purge.calc_virtual(CounterState(power=-5001, currents=[7.25]*3, exported=200, imported=100))

    # evaluation
    assert vars(state) == vars(params.expected_state)
