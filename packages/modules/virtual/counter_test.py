import threading
from typing import Callable
from unittest.mock import Mock

import pytest

from control.chargepoint import Chargepoint
from control.counter import CounterAll
from control import data
from modules.common.component_state import CounterState
from modules.virtual import counter
from modules.virtual.config import VirtualCounterConfiguration, VirtualCounterSetup


@pytest.fixture(autouse=True)
def init_data() -> None:
    data.data_init(threading.Event())
    data.data.counter_data["all"] = CounterAll()
    data.data.counter_data["all"].data = {"get": {"hierarchy": [{"id": 0, "type": "counter", "children": [
        {"id": 6, "type": "counter", "children": [
            {"id": 3, "type": "cp", "children": []}, {"id": 4, "type": "cp", "children": []}]}]}]}}
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
def test_virtual_counter(monkeypatch, params):
    # setup
    mock_counter_value_store = Mock()
    monkeypatch.setattr(counter, "get_counter_value_store", Mock(return_value=mock_counter_value_store))
    c = counter.VirtualCounter(0, VirtualCounterSetup(
        id=6, configuration=VirtualCounterConfiguration(external_consumption=0)))
    params.init_func()

    # execution
    c.update()

    # evaluation
    counter_state = mock_counter_value_store.set.call_args[0][0]
    assert counter_state.currents == params.expected_state.currents
