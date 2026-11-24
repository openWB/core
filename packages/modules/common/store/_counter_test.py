# bad integration test

from typing import Callable, NamedTuple
from unittest.mock import Mock

import pytest


from control import data
from control.chargepoint.chargepoint import Chargepoint
from control.counter import Counter, CounterData, Get
from control.counter_all.counter_all import CounterAll
from helpermodules import timecheck
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import _wire_sustained_error_handler
from modules.common.fault_state import ComponentInfo, FaultState
from modules.chargepoints.mqtt.chargepoint_module import ChargepointModule
from modules.common.component_state import BatState, ChargepointState, CounterState, InverterState
from modules.common.component_type import ComponentType
from modules.common.simcount._simcounter import SimCounter
from modules.common.store import _counter
from modules.common.store._api import LoggingValueStore
from modules.common.store._api import update_values
from modules.common.store._battery import BatteryValueStoreBroker, PurgeBatteryState
from modules.common.store._counter import CounterValueStoreBroker, PurgeCounterState
from modules.common.store._inverter import InverterValueStoreBroker, PurgeInverterState
from modules.devices.generic.mqtt.bat import MqttBat
from modules.devices.generic.mqtt.counter import MqttCounter
from modules.devices.generic.mqtt.inverter import MqttInverter


@pytest.fixture(autouse=True)
def mock_data() -> None:
    data.data_init(Mock())
    data.data.counter_all_data = CounterAll()
    data.data.counter_all_data.data.get.hierarchy = []


@pytest.mark.parametrize("prior_read", [False, True])
def test_counter_sustained_read_error_zeroes_and_publishes_without_hierarchy(prior_read, monkeypatch, mock_pub):
    now = 1000
    monkeypatch.setattr(timecheck, "create_timestamp", lambda: now)
    store = _counter.get_counter_value_store(9)
    component = Mock(store=store, fault_state=FaultState(ComponentInfo(9, "HTTP-Zähler", "counter")))
    _wire_sustained_error_handler(component)
    if prior_read:
        store.set(CounterState(power=1234, imported=100, exported=50,
                               powers=[230, 460, 544], currents=[1, 2, 2.4], voltages=[229, 230, 231]))

    with SingleComponentUpdateContext(component.fault_state):
        raise Exception("HTTP 404")
    assert not any(call.args[0].endswith("/get/power") for call in mock_pub.pub.call_args_list)

    now += 61
    with SingleComponentUpdateContext(component.fault_state):
        raise Exception("HTTP 404")

    assert store.delegate.delegate.state.power == 0
    mock_pub.pub.assert_any_call("openWB/set/counter/9/get/power", 0)
    mock_pub.pub.assert_any_call("openWB/set/counter/9/get/powers", [0.0]*3)
    mock_pub.pub.assert_any_call("openWB/set/counter/9/get/currents", [0.0]*3)
    if prior_read:
        assert store.delegate.delegate.state.imported == 100
        assert store.delegate.delegate.state.exported == 50
        assert store.delegate.delegate.state.voltages == [229, 230, 231]

    # Ein erfolgreicher neuer Abruf ersetzt die Nullung wieder durch den Messwert.
    with SingleComponentUpdateContext(component.fault_state):
        store.set(CounterState(power=789, imported=101, exported=50,
                               powers=[230, 230, 329], currents=[1, 1, 1.4]))
    update_values(component)
    assert store.delegate.delegate.state.power == 789
    mock_pub.pub.assert_any_call("openWB/set/counter/9/get/power", 789)
    mock_pub.pub.assert_any_call("openWB/set/counter/9/get/powers", [230, 230, 329])
    mock_pub.pub.assert_any_call("openWB/set/counter/9/get/currents", [1, 1, 1.4])


def test_counter_zeroes_power_after_virtual_calculation(monkeypatch, mock_pub):
    store = _counter.get_counter_value_store(9, add_child_values=True)
    store.set(CounterState(power=1234))
    calc_virtual = Mock(return_value=CounterState(power=5678, imported=100, exported=50,
                                                  powers=[1000, 2000, 2678], currents=[4, 8, 12]))
    monkeypatch.setattr(store, "calc_virtual", calc_virtual)

    store.zero_power_on_sustained_error()
    store.update()

    calc_virtual.assert_called_once()
    assert store.delegate.delegate.state.power == 0
    assert store.delegate.delegate.state.powers == [0.0]*3
    assert store.delegate.delegate.state.currents == [0.0]*3
    assert store.delegate.delegate.state.imported == 100
    assert store.delegate.delegate.state.exported == 50
    mock_pub.pub.assert_any_call("openWB/set/counter/9/get/power", 0)


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
                                                                                            exported=0,
                                                                                            phases_in_use=3,
                                                                                            plug_state=True,
                                                                                            charge_state=True)))))


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
                              simcounter=SimCounter(0, 0, ComponentType.COUNTER))
    original_get_hierarchy_obj_by_id = _counter.get_hierarchy_obj_by_id
    mock_comp_obj_iter = iter(params.mock_comp)

    def mock_get_hierarchy_obj_by_id(component_id, component_type):
        if component_type == ComponentType.CHARGEPOINT.value:
            return original_get_hierarchy_obj_by_id(component_id, component_type)
        return next(mock_comp_obj_iter)

    monkeypatch.setattr(_counter, "get_hierarchy_obj_by_id", mock_get_hierarchy_obj_by_id)

    # execution
    state = purge.calc_virtual(CounterState(power=-5001, currents=[7.25]*3, exported=200, imported=100))

    # evaluation
    assert vars(state) == vars(params.expected_state)


def test_calc_uncounted_consumption(monkeypatch):
    """
    Test für calc_uncounted_consumption mit folgendem Szenario:
    - Übergeordnete Ebene: Ein Zähler (id=0, parent counter)
    - Gleiche Ebene wie virtueller Zähler: Ein Ladepunkt (id=1) und ein weiterer Zähler (id=2)
    - Virtueller Zähler: id=3 (soll nicht-gezählten Verbrauch berechnen)

    Hierarchie:
    Counter 0 (parent, 8000W, 1kWh importiert, 0.5kWh exportiert)
    ├── Chargepoint 1 (3000W, 150Wh importiert, 0Wh exportiert)
    ├── Counter 2 (2000W, 300Wh importiert, 100Wh exportiert)
    └── Virtual Counter 3 (uncounted: 8000 - 3000 - 2000 = 3000W, 0.15kWh imp, 0kWh exp)
    """
    # setup
    data.data_init(Mock())
    data.data.counter_all_data = CounterAll()
    data.data.counter_all_data.data.get.hierarchy = [
        {
            "id": 0,
            "type": "counter",
            "children": [
                {"id": 1, "type": "cp", "children": []},
                {"id": 2, "type": "counter", "children": []},
                {"id": 3, "type": "counter", "children": []}
            ]
        }
    ]

    data.data.counter_data["counter0"] = Mock(
        spec=Counter,
        data=Mock(
            spec=CounterData,
            get=Mock(
                spec=Get,
                power=8000,
                exported=500,
                imported=1000,
                currents=[20.0, 22.0, 18.0]
            )
        )
    )

    add_chargepoint(1)
    data.data.cp_data["cp1"].data.get.power = 3000
    data.data.cp_data["cp1"].data.get.currents = [8.0, 9.0, 7.0]
    data.data.cp_data["cp1"].chargepoint_module.store.delegate.state.power = 3000
    data.data.cp_data["cp1"].chargepoint_module.store.delegate.state.currents = [8.0, 9.0, 7.0]
    data.data.cp_data["cp1"].chargepoint_module.store.delegate.state.imported = 150
    data.data.cp_data["cp1"].chargepoint_module.store.delegate.state.exported = 0

    data.data.counter_data["counter2"] = Mock(
        spec=Counter,
        data=Mock(
            spec=CounterData,
            get=Mock(
                spec=Get,
                power=2000,
                exported=100,
                imported=300,
                currents=[5.0, 6.0, 4.0]
            )
        )
    )

    parent_counter_component = Mock()
    parent_counter_component.component_config.type = "counter"
    parent_counter_component.store.add_child_values = False

    regular_counter_component = Mock(
        spec=MqttCounter,
        store=Mock(
            spec=PurgeCounterState,
            delegate=Mock(
                spec=LoggingValueStore,
                delegate=Mock(
                    spec=CounterValueStoreBroker,
                    state=CounterState(
                        power=2000,
                        exported=100,
                        imported=300,
                        currents=[5.0, 6.0, 4.0]
                    )
                )
            )
        )
    )

    original_get_hierarchy_obj_by_id = _counter.get_hierarchy_obj_by_id

    def mock_get_hierarchy_obj_by_id(component_id, component_type):
        if component_id == 0:  # Parent counter
            return parent_counter_component
        elif component_id == 2:  # Regular counter
            return regular_counter_component
        return original_get_hierarchy_obj_by_id(component_id, component_type)

    monkeypatch.setattr(_counter, "get_hierarchy_obj_by_id", mock_get_hierarchy_obj_by_id)

    virtual_counter_purge = PurgeCounterState(
        delegate=Mock(delegate=Mock(num=3)),
        add_child_values=True,
        simcounter=SimCounter(0, 0, "counter")
    )

    # execution
    result_state = virtual_counter_purge.calc_virtual(CounterState())

    # evaluation
    # Erwartete Werte: Parent Counter - (Chargepoint + Regular Counter)
    # Power: 8000 - (3000 + 2000) = 3000W
    # Currents: [20.0, 22.0, 18.0] - ([8.0, 9.0, 7.0] + [5.0, 6.0, 4.0]) = [7.0, 7.0, 7.0]
    # Imported: 1000 - (150 + 300) = 550
    # Exported: 500 - (0 + 100) = 400

    expected_state = CounterState(
        power=3000,
        currents=[7.0, 7.0, 7.0],
        imported=150,
        exported=0
    )

    assert vars(result_state) == vars(expected_state)
