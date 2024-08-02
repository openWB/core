import threading
from typing import Callable
from unittest.mock import Mock

import pytest

from control import data
from control.chargepoint.chargepoint import Chargepoint
from control.counter_all import CounterAll
from modules.common.component_state import CounterState
from modules.devices.generic.virtual import counter
from modules.devices.generic.virtual.config import VirtualCounterConfiguration, VirtualCounterSetup
from packages.conftest import hierarchy_standard, hierarchy_hybrid, hierarchy_nested


@pytest.fixture(autouse=True)
def init_data() -> None:
    data.data_init(threading.Event())
    data.data.counter_all_data = CounterAll()
    data.data.counter_all_data.data.get.hierarchy = [{"id": 0, "type": "counter", "children": [
        {"id": 6, "type": "counter", "children": [
            {"id": 3, "type": "cp", "children": []}, {"id": 4, "type": "cp", "children": []}]}]}]
    data.data.cp_data["cp3"] = Chargepoint(3, None)
    data.data.cp_data["cp3"].data.get.currents = [16, 16, 0]
    data.data.cp_data["cp4"] = Chargepoint(4, None)
    data.data.cp_data["cp4"].data.get.currents = [16, 16, 16]


def init_twisted_cp() -> None:
    data.data.cp_data["cp3"].data.config.phase_1 = 2
    data.data.cp_data["cp4"].data.config.phase_1 = 1


def init_parallel_cp() -> None:
    data.data.cp_data["cp3"].data.config.phase_1 = 1
    data.data.cp_data["cp4"].data.config.phase_1 = 1


class Params:
    def __init__(self, name: str, init_func: Callable[[], None], expected_state: CounterState) -> None:
        self.name = name
        self.init_func = init_func
        self.expected_state = expected_state


cases = [Params("twisted cp", init_twisted_cp, CounterState(currents=[16, 32, 32])),
         Params("parallel cp", init_parallel_cp, CounterState(currents=[32, 32, 16]))]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_virtual_counter(mock_pub: Mock, params):
    # setup
    c = counter.VirtualCounter(0, VirtualCounterSetup(
        id=6, configuration=VirtualCounterConfiguration(external_consumption=0)))
    params.init_func()

    # execution
    c.update()
    c.store.update()

    # evaluation
    for call in mock_pub.mock_calls:
        try:
            if call.args[0] == 'openWB/set/counter/6/get/currents':
                assert params.expected_state.currents == call.args[1]
                break
        except IndexError:
            pass
    else:
        pytest.fail("Topic openWB/set/counter/6/get/currents is missing")


@pytest.mark.parametrize("counter_all",
                         [pytest.param(hierarchy_standard, id="standard"),
                          pytest.param(hierarchy_hybrid, id="hybrid"),
                          pytest.param(hierarchy_nested, id="nested")])
def test_virtual_counter_hierarchies(counter_all: Callable[[], CounterAll], data_, mock_pub: Mock):
    # setup
    virtual_counter = counter.VirtualCounter(0, VirtualCounterSetup(
        id=0, configuration=VirtualCounterConfiguration(external_consumption=0)))
    data.data.counter_all_data = counter_all()

    # execution
    virtual_counter.update()
    virtual_counter.store.update()

    # evaluation
    for call in mock_pub.mock_calls:
        try:
            if call.args[0] == 'openWB/set/counter/0/get/power':
                assert 5700 == call.args[1]
                break
        except IndexError:
            pass
    else:
        pytest.fail("Topic openWB/set/counter/6/get/currents is missing")
