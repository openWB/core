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
                              simcounter=SimCounter(0, 0, prefix="bezug"))
    mock_comp_obj = Mock(side_effect=params.mock_comp)
    monkeypatch.setattr(_counter, "get_component_obj_by_id", mock_comp_obj)

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
    Counter 0 (parent, 8000W total)
    ├── Chargepoint 1 (3000W)
    ├── Counter 2 (2000W) 
    └── Virtual Counter 3 (uncounted: 8000 - 3000 - 2000 = 3000W)
    """
    # setup
    data.data_init(Mock())
    data.data.counter_all_data = CounterAll()

    # Setup parent counter (id=0) auf übergeordneter Ebene
    data.data.counter_data["counter0"] = Mock(
        spec=Counter,
        data=Mock(
            spec=CounterData,
            get=Mock(
                spec=Get,
                power=8000,  # Gesamtverbrauch
                exported=500,
                imported=1000,
                currents=[20.0, 22.0, 18.0]  # Gesamtstrom
            )
        )
    )

    # Setup Ladepunkt (id=1) auf gleicher Ebene wie virtueller Zähler
    add_chargepoint(1)
    data.data.cp_data["cp1"].data.get.power = 3000
    data.data.cp_data["cp1"].data.get.currents = [8.0, 9.0, 7.0]
    data.data.cp_data["cp1"].chargepoint_module.store.delegate.state.power = 3000
    data.data.cp_data["cp1"].chargepoint_module.store.delegate.state.currents = [8.0, 9.0, 7.0]
    data.data.cp_data["cp1"].chargepoint_module.store.delegate.state.imported = 150
    data.data.cp_data["cp1"].chargepoint_module.store.delegate.state.exported = 0

    # Setup weiterer Zähler (id=2) auf gleicher Ebene
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

    # Hierarchie: Parent Counter 0 hat Kinder: CP 1, Counter 2, Virtual Counter 3
    data.data.counter_all_data.data.get.hierarchy = [
        {
            "id": 0,
            "type": "counter",
            "children": [
                {"id": 1, "type": "cp", "children": []},
                {"id": 2, "type": "counter", "children": []},
                {"id": 3, "type": "counter", "children": []}  # Virtual counter
            ]
        }
    ]

    # Mock für Parent-Lookup
    def mock_get_parent_of_element(element_id):
        if element_id == 3:  # Virtual counter
            return 0  # Parent counter
        return None

    # Mock für get_elements_for_downstream_calculation
    def mock_get_elements_for_downstream_calculation(parent_id):
        if parent_id == 0:  # Parent counter
            return [
                {"id": 1, "type": "cp"},
                {"id": 2, "type": "counter"}
                # Virtual counter 3 wird nicht in eigene Berechnung einbezogen
            ]
        return []

    data.data.counter_all_data.get_parent_of_element = Mock(side_effect=mock_get_parent_of_element)
    data.data.counter_all_data.get_elements_for_downstream_calculation = Mock(
        side_effect=mock_get_elements_for_downstream_calculation
    )

    # Mock parent counter component
    parent_counter_component = Mock()
    parent_counter_component.component_config.type = "counter"
    parent_counter_component.store.add_child_values = False  # Nicht virtuell

    # Mock regular counter component (id=2)
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

    def mock_get_component_obj_by_id(component_id):
        if component_id == 0:  # Parent counter
            return parent_counter_component
        elif component_id == 2:  # Regular counter
            return regular_counter_component
        return None

    monkeypatch.setattr(_counter, "get_component_obj_by_id", mock_get_component_obj_by_id)

    # Setup virtual counter (id=3)
    virtual_counter_purge = PurgeCounterState(
        delegate=Mock(delegate=Mock(num=3)),
        add_child_values=True,
        simcounter=SimCounter(0, 0, prefix="virtual")
    )

    # execution
    result_state = virtual_counter_purge.calc_uncounted_consumption()

    # evaluation
    # Erwartete Werte: Parent Counter - (Chargepoint + Regular Counter)
    # Power: 8000 - (3000 + 2000) = 3000W
    # Currents: [20.0, 22.0, 18.0] - ([8.0, 9.0, 7.0] + [5.0, 6.0, 4.0]) = [7.0, 7.0, 7.0]
    # Imported: 1000 - (150 + 300) = 550
    # Exported: 500 - (0 + 100) = 400

    expected_state = CounterState(
        power=3000,
        currents=[7.0, 7.0, 7.0],
        imported=550,
        exported=400
    )

    assert vars(result_state) == vars(expected_state)
