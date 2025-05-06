# bad integration test

from typing import Callable, NamedTuple
from unittest.mock import Mock

import pytest


from control import data
from control.chargepoint.chargepoint import Chargepoint
from control.counter import Counter, CounterData, Get
from control.counter_all import CounterAll
from modules.chargepoints.mqtt.chargepoint_module import ChargepointModule
from modules.common.component_state import BatState, ChargepointState, CounterState, InverterState
from modules.common.simcount._simcounter import SimCounter
from modules.common.store import _counter
from modules.common.store._api import LoggingValueStore
from modules.common.store._battery import BatteryValueStoreBroker, PurgeBatteryState
from modules.common.store._counter import PurgeCounterState
from modules.common.store._inverter import InverterValueStoreBroker, PurgeInverterState
from modules.devices.generic.mqtt.bat import MqttBat
from modules.devices.generic.mqtt.counter import MqttCounter
from modules.devices.generic.mqtt.inverter import MqttInverter


@pytest.fixture(autouse=True)
def mock_data() -> None:
    data.data_init(Mock())
    data.data.counter_all_data = CounterAll()
    data.data.counter_all_data.data.get.hierarchy = []


def add_chargepoint(id: int):
    data.data.cp_data[f"cp{id}"] = Mock(spec=Chargepoint,
                                        id=id,
                                        data=Mock(
                                            config=Mock(phase_1=1),
                                            get=Mock(power=13359,
                                                     currents=[19.36, 19.36, 19.36],
                                                     imported=0,
                                                     exported=0)),
                                        chargepoint_module=Mock(
                                            spec=ChargepointModule,
                                            store=Mock(spec=LoggingValueStore,
                                                       delegate=Mock(spec=LoggingValueStore,
                                                                     state=ChargepointState(power=13359,
                                                                                            currents=[
                                                                                                19.36, 19.36, 19.36],
                                                                                            imported=0,
                                                                                            exported=0)))))


def mock_data_standard():
    add_chargepoint(3)
    data.data.counter_all_data.data.get.hierarchy = [{"id": 0, "type": "counter",
                                                      "children": [{"id": 3, "type": "cp", "children": []}]},
                                                     {"id": 1, "type": "inverter", "children": []},
                                                     {"id": 2, "type": "bat", "children": []}]


def mock_data_nested():
    add_chargepoint(1)
    add_chargepoint(3)
    data.data.counter_data["counter2"] = Mock(
        spec=Counter, data=Mock(spec=CounterData, get=Mock(
            spec=Get, power=13359, exported=0, imported=0, currents=[19.36, 19.36, 19.36])))
    data.data.counter_all_data.data.get.hierarchy = [
        {"id": 0, "type": "counter",
         "children": [{"id": 1, "type": "cp", "children": []},
                      {"id": 2, "type": "counter",
                       "children": [
                           {"id": 3, "type": "cp", "children": []}]}]}]


mock_comp_obj_inv_bat = [
    Mock(spec=MqttBat,
         store=Mock(spec=PurgeBatteryState,
                    delegate=Mock(spec=LoggingValueStore,
                                  delegate=Mock(spec=BatteryValueStoreBroker,
                                                state=BatState(power=223,
                                                               exported=200,
                                                               imported=100))))),
    Mock(spec=MqttInverter,
         store=Mock(spec=PurgeInverterState,
                    delegate=Mock(spec=LoggingValueStore,
                                  delegate=Mock(spec=InverterValueStoreBroker,
                                                state=InverterState(power=5786,
                                                                    exported=2000)))))]

mock_comp_obj_counter_inv_bat = [Mock(spec=MqttCounter,
                                      store=Mock(spec=_counter.PurgeCounterState,
                                                 delegate=Mock(spec=LoggingValueStore,
                                                               delegate=Mock(spec=_counter.CounterValueStoreBroker,
                                                                             state=CounterState(power=13359,
                                                                                                exported=0,
                                                                                                imported=0,
                                                                                                currents=[19.36]*3))))),
                                 Mock(spec=MqttBat,
                                      store=Mock(spec=PurgeBatteryState,
                                                 delegate=Mock(spec=LoggingValueStore,
                                                               delegate=Mock(spec=BatteryValueStoreBroker,
                                                                             state=BatState(power=223,
                                                                                            exported=200,
                                                                                            imported=100))))),
                                 Mock(spec=MqttInverter,
                                      store=Mock(spec=PurgeInverterState,
                                                 delegate=Mock(spec=LoggingValueStore,
                                                               delegate=Mock(spec=InverterValueStoreBroker,
                                                                             state=InverterState(power=5786,
                                                                                                 exported=2000)))))
                                 ]

Params = NamedTuple("Params", [("name", str), ("mock_comp", Mock),
                    ("mock_data", Callable), ("expected_state", CounterState)])
cases = [
    Params("standard", mock_comp_obj_inv_bat, mock_data_standard, CounterState(
        power=8358, currents=[26.61]*3, exported=200, imported=100)),
    Params("nested virtual", mock_comp_obj_counter_inv_bat, mock_data_nested, CounterState(
        power=21717, currents=[45.97]*3, exported=200, imported=100))
]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_calc_virtual(params: Params, monkeypatch):
    # setup
    params.mock_data()
    purge = PurgeCounterState(delegate=Mock(delegate=Mock(num=0)),
                              add_child_values=True,
                              simcounter=SimCounter(0, 0, prefix="bezug"))
    mock_comp_obj = Mock(side_effect=params.mock_comp)
    monkeypatch.setattr(_counter, "get_component_obj_by_id", mock_comp_obj)

    # execution
    state = purge.calc_virtual(CounterState(power=-5001, currents=[7.25]*3, exported=200, imported=100))

    # evaluation
    assert vars(state) == vars(params.expected_state)
