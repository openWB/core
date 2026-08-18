from typing import Callable
from unittest.mock import Mock
import pytest

from control import data


from control.bat import Bat, BatData
from control.bat import Get as BatGet
from control.bat import Set as BatSet
from control.chargepoint.chargepoint import Chargepoint, ChargepointData
from control.chargepoint.chargepoint_data import Config, Get, Set
from control.counter import Counter, CounterData, CounterMode
from control.counter import Config as CounterConfig
from control.counter import Get as CounterGet
from control.counter_all import CounterAll
from control.pv import Pv, PvData
from control.pv import Config as PvConfig
from control.pv import Get as PvGet

from modules.chargepoints.mqtt.chargepoint_module import ChargepointModule
from modules.common.component_state import ChargepointState
from modules.common.store._api import LoggingValueStore

from packages.conftest import (
    hierarchy_standard,
    hierarchy_hybrid,
    hierarchy_nested)
from modules.common.fault_state import FaultStateLevel


@pytest.mark.parametrize("counter_all",
                         [pytest.param(hierarchy_standard, id="standard"),
                          pytest.param(hierarchy_hybrid, id="hybrid"),
                             pytest.param(hierarchy_nested, id="nested")
                          ])
def test_calc_home_consumption(counter_all: Callable[[], CounterAll], data_):
    c = counter_all()
    home_consumption = c._calc_home_consumption()[0]
    assert home_consumption == 500


@pytest.mark.parametrize(
    ["counter_all", "expected_home_consumption"],
    [
        pytest.param("hierarchy_home_consumption_standard", 0, id="hierarchy_home_consumption_standard"),
        pytest.param("hierarchy_home_consumption_hybrid", 500, id="hierarchy_home_consumption_hybrid"),
        pytest.param("hierarchy_nested_home_consumption_level_3", 500, id="hierarchy_nested_home_consumption_level_3"),
        pytest.param("hierarchy_nested_home_consumption_level_2",
                     500, id="hierarchy_nested_home_consumption_level_2"),
        pytest.param("hierarchy_home_consumption_only_root",
                     1000, id="hierarchy_home_consumption_only_root"),
        pytest.param("hierarchy_home_consumption_all",
                     1000, id="hierarchy_home_consumption_all"),
        pytest.param("hierarchy_nested_home_consumption_multi_level_2", 250,
                     id="hierarchy_nested_home_consumption_multi_level_2"),
        pytest.param("hierarchy_nested_home_consumption_2_hc_childs", 500,
                     id="hierarchy_nested_home_consumption_2_hc_childs")
    ],
)
def test_calc_home_consumption_with_configured_home_consumption_counter(
    counter_all: str,
    expected_home_consumption: int,
    data_home_consumption,
):
    c = globals()[counter_all]()
    home_consumption = c._calc_home_consumption()[0]
    assert home_consumption == expected_home_consumption


@pytest.mark.parametrize(["home_consumption",
                          "invalid_home_consumption",
                          "expected_home_consumption",
                          "expected_invalid_home_consumption"],
                         [pytest.param(500, 0, 500, 0, id="valid home consumption"),
                          pytest.param(-100, 0, 200, 1, id="first invalid home consumption"),
                          pytest.param(-100, 3, 0, 3, id="invalid home consumption, reset home consumption")])
def test_set_home_consumption(home_consumption: int,
                              invalid_home_consumption: int,
                              expected_home_consumption: int,
                              expected_invalid_home_consumption: int,
                              monkeypatch,
                              data_):
    # setup
    c = hierarchy_standard()
    data.data.counter_data["counter0"].data.get.fault_state = FaultStateLevel.NO_ERROR
    c.data.set.invalid_home_consumption = invalid_home_consumption
    c.data.set.home_consumption = 200
    calc_home_consumption_mock = Mock(return_value=[home_consumption, []])
    monkeypatch.setattr(CounterAll, "_calc_home_consumption", calc_home_consumption_mock)

    # execution
    c.set_home_consumption()

    # evaluation
    assert c.data.set.invalid_home_consumption == expected_invalid_home_consumption
    assert c.data.set.home_consumption == expected_home_consumption


def hierarchy_home_consumption_standard() -> CounterAll:
    # counter0
    #        |
    #        - cp4
    #        - cp5
    #        - cp3
    #        - inverter1
    #        - bat2
    # counter_8 <-- home consumption counter
    #

    # UnbekannterVerbraucher/Hausverbrauch am Countern
    # counter0 = 750
    # counter8 = 500
    # Final Home Consumption = 0
    c = CounterAll()
    c.data.get.hierarchy = [{"id": 0, "type": "counter",
                             "children": [
                                 {"id": 4, "type": "cp", "children": []},
                                 {"id": 5, "type": "cp", "children": []},
                                 {"id": 3, "type": "cp", "children": []},
                                 {"id": 1, "type": "inverter", "children": []},
                                 {"id": 2, "type": "bat", "children": []}]},
                            {"id": 8, "type": "counter",
                             "children": []}]
    return c


def hierarchy_home_consumption_hybrid() -> CounterAll:
    # counter0
    #        |
    #        - cp3
    #        - cp4
    #        - counter8  <-- home consumption counter
    #                  |
    #                   - cp5
    #        - inverter1
    #        - bat2

    # UnbekannterVerbraucher/Hausverbrauch am Countern
    # counter0 = 250
    # counter8 = 500
    # Final Home Consumption = 500
    c = CounterAll()
    c.data.get.hierarchy = [{"id": 0, "type": "counter",
                             "children": [
                                 {"id": 3, "type": "cp", "children": []},
                                 {"id": 4, "type": "cp", "children": []},
                                 {"id": 8, "type": "counter",
                                  "children": [
                                      {"id": 5, "type": "cp", "children": []}]},
                                 {"id": 1, "type": "inverter", "children": []},
                                 {"id": 2, "type": "bat", "children": []}]}]
    return c


def hierarchy_nested_home_consumption_level_3() -> CounterAll:
    # counter0
    #        |
    #        - cp3
    #        - counter6
    #                  |
    #                   - cp4
    #                   - counter8  <-- home consumption counter
    #                             |
    #                              - cp5
    #                   - inverter1
    #        - bat2

    # UnbekannterVerbraucher/Hausverbrauch am Countern
    # counter0 = 250
    # counter6 = 0
    # counter8 = 500
    # Final Home Consumption = 500
    c = CounterAll()
    c.data.get.hierarchy = [{"id": 0, "type": "counter",
                             "children": [
                                 {"id": 3, "type": "cp", "children": []},
                                 {"id": 6, "type": "counter",
                                  "children": [
                                      {"id": 4, "type": "cp", "children": []},
                                      {"id": 8, "type": "counter",
                                       "children": [
                                           {"id": 5, "type": "cp", "children": []}]},
                                      {"id": 1, "type": "inverter", "children": []}
                                  ]},
                                 {"id": 2, "type": "bat", "children": []}]}]
    return c


def hierarchy_nested_home_consumption_level_2() -> CounterAll:
    # counter0
    #        |
    #        - cp3
    #        - counter9 <-- home consumption counter
    #                  |
    #                   - cp4
    #                   - counter10  <-- home consumption counter
    #                             |
    #                              - cp5
    #
    #                   - inverter1
    #        - bat2

    # UnbekannterVerbraucher/Hausverbrauch am Countern
    # counter0 = 250
    # coutner9 = 250
    # counter10 = 250
    # Final Home Consumption = 500
    c = CounterAll()
    c.data.get.hierarchy = [{"id": 0, "type": "counter",
                             "children": [
                                 {"id": 3, "type": "cp", "children": []},
                                 {"id": 9, "type": "counter",
                                  "children": [
                                      {"id": 4, "type": "cp", "children": []},
                                      {"id": 10, "type": "counter",
                                       "children": [
                                           {"id": 5, "type": "cp", "children": []}]},
                                      {"id": 1, "type": "inverter", "children": []},
                                  ]},
                                 {"id": 2, "type": "bat", "children": []}]}]
    return c


def hierarchy_home_consumption_only_root() -> CounterAll:
    # counter11  <-- home consumption counter
    #        |
    #        - cp3
    #        - counter16
    #                  |
    #                   - cp4
    #                   - counter17
    #                             |
    #                              - cp5
    #
    #                   - inverter1
    #        - bat2

    # UnbekannterVerbraucher/Hausverbrauch am Countern
    # counter11 = 500
    # coutner16 = 250
    # counter17 = 250
    # Final Home Consumption = 1000
    c = CounterAll()
    c.data.get.hierarchy = [{"id": 11, "type": "counter",
                             "children": [
                                 {"id": 3, "type": "cp", "children": []},
                                 {"id": 16, "type": "counter",
                                  "children": [
                                      {"id": 4, "type": "cp", "children": []},
                                      {"id": 17, "type": "counter",
                                       "children": [
                                           {"id": 5, "type": "cp", "children": []}]},
                                      {"id": 1, "type": "inverter", "children": []},
                                  ]},
                                 {"id": 2, "type": "bat", "children": []}]}]
    return c


def hierarchy_home_consumption_all() -> CounterAll:
    # counter11  <-- home consumption counter
    #        |
    #        - cp3
    #        - counter9  <-- home consumption counter
    #                  |
    #                   - cp4
    #                   - counter10  <-- home consumption counter
    #                             |
    #                              - cp5
    #
    #                   - inverter1
    #        - bat2

    # UnbekannterVerbraucher/Hausverbrauch am Countern
    # counter11 = 500
    # coutner9 = 250
    # counter10 = 250
    # Final Home Consumption = 1000
    c = CounterAll()
    c.data.get.hierarchy = [{"id": 11, "type": "counter",
                             "children": [
                                 {"id": 3, "type": "cp", "children": []},
                                 {"id": 9, "type": "counter",
                                  "children": [
                                      {"id": 4, "type": "cp", "children": []},
                                      {"id": 10, "type": "counter",
                                       "children": [
                                           {"id": 5, "type": "cp", "children": []}]},
                                      {"id": 1, "type": "inverter", "children": []},
                                  ]},
                                 {"id": 2, "type": "bat", "children": []}]}]
    return c


def hierarchy_nested_home_consumption_multi_level_2() -> CounterAll:
    # counter0
    #        |
    #        - cp3
    #        - counter6
    #                  |
    #                   - cp4
    #                   - counter10  <-- home consumption counter
    #                             |
    #                              - cp5
    #                   - counter14
    #                             |
    #                              - inverter1
    #        - bat2

    # UnbekannterVerbraucher/Hausverbrauch am Countern
    # counter0 = 250
    # coutner6 = 0
    # counter10 = 250
    # counter14 = 250
    # Final Home Consumption = 250
    c = CounterAll()
    c.data.get.hierarchy = [{"id": 0, "type": "counter",
                             "children": [
                                 {"id": 3, "type": "cp", "children": []},
                                 {"id": 6, "type": "counter",
                                  "children": [
                                      {"id": 4, "type": "cp", "children": []},
                                      {"id": 10, "type": "counter",
                                       "children": [
                                           {"id": 5, "type": "cp", "children": []}]},
                                      {"id": 14, "type": "counter",
                                       "children": [
                                           {"id": 1, "type": "inverter", "children": []}]},
                                  ]},
                                 {"id": 2, "type": "bat", "children": []}]}]
    return c


def hierarchy_nested_home_consumption_2_hc_childs() -> CounterAll:
    # counter0
    #        |
    #        - cp3
    #        - counter6
    #                  |
    #                   - cp4
    #                   - counter10  <-- home consumption counter
    #                             |
    #                              - cp5
    #                   - counter15 <-- home consumption counter
    #                             |
    #                              - inverter1
    #        - bat2

    # UnbekannterVerbraucher/Hausverbrauch am Countern
    # counter0 = 250
    # coutner6 = 0
    # counter10 = 250
    # counter15 = 250
    # Final Home Consumption = 500
    c = CounterAll()
    c.data.get.hierarchy = [{"id": 0, "type": "counter",
                             "children": [
                                 {"id": 3, "type": "cp", "children": []},
                                 {"id": 6, "type": "counter",
                                  "children": [
                                      {"id": 4, "type": "cp", "children": []},
                                      {"id": 10, "type": "counter",
                                       "children": [
                                           {"id": 5, "type": "cp", "children": []}]},
                                      {"id": 15, "type": "counter",
                                       "children": [
                                           {"id": 1, "type": "inverter", "children": []}]},
                                  ]},
                                 {"id": 2, "type": "bat", "children": []}]}]
    return c


@pytest.fixture()
def data_home_consumption() -> None:
    data.data_init(Mock())
    data.data.cp_data = {
        "cp3": Mock(spec=Chargepoint, data=Mock(spec=ChargepointData,
                                                config=Mock(spec=Config, phase_1=1),
                                                get=Mock(spec=Get, currents=[30, 0, 0], power=6900,
                                                         daily_imported=10000, daily_exported=0, imported=56000,
                                                         fault_state=0),
                                                set=Mock(spec=Set, loadmanagement_available=True)),
                    chargepoint_module=Mock(spec=ChargepointModule,
                                            store=Mock(spec=LoggingValueStore,
                                                       delegate=Mock(spec=LoggingValueStore,
                                                                     state=ChargepointState(currents=[30, 0, 0],
                                                                                            power=6900,
                                                                                            plug_state=False,
                                                                                            charge_state=False,
                                                                                            imported=None,
                                                                                            exported=None,
                                                                                            phases_in_use=0))))),
        "cp4": Mock(spec=Chargepoint, data=Mock(spec=ChargepointData,
                                                config=Mock(spec=Config, phase_1=2),
                                                get=Mock(spec=Get, currents=[0, 15, 15], power=6900,
                                                         daily_imported=10000, daily_exported=0, imported=60000,
                                                         fault_state=0),
                                                set=Mock(spec=Set, loadmanagement_available=True)),
                    chargepoint_module=Mock(spec=ChargepointModule,
                                            store=Mock(spec=LoggingValueStore,
                                                       delegate=Mock(spec=LoggingValueStore,
                                                                     state=ChargepointState(currents=[0, 15, 15],
                                                                                            power=6900,
                                                                                            plug_state=False,
                                                                                            charge_state=False,
                                                                                            imported=None,
                                                                                            exported=None,
                                                                                            phases_in_use=0))))),
        "cp5": Mock(spec=Chargepoint, data=Mock(spec=ChargepointData,
                                                config=Mock(spec=Config, phase_1=3),
                                                get=Mock(spec=Get, currents=[10]*3, power=6900,
                                                         daily_imported=10000, daily_exported=0, imported=62000,
                                                         fault_state=0),
                                                set=Mock(spec=Set, loadmanagement_available=True)),
                    chargepoint_module=Mock(spec=ChargepointModule,
                                            store=Mock(spec=LoggingValueStore,
                                                       delegate=Mock(spec=LoggingValueStore,
                                                                     state=ChargepointState(currents=[10]*3,
                                                                                            power=6900,
                                                                                            plug_state=False,
                                                                                            charge_state=False,
                                                                                            imported=None,
                                                                                            exported=None,
                                                                                            phases_in_use=0)))))}
    data.data.bat_data.update({"bat2": Mock(spec=Bat, num=2, data=Mock(spec=BatData, get=Mock(
        spec=BatGet, power=-5000, fault_state=0),
        set=Mock(spec=BatSet, power_limit=None)))})
    data.data.pv_data.update({"pv1": Mock(spec=Pv, data=Mock(
        spec=PvData, get=Mock(spec=PvGet, power=-10000, fault_state=0), config=Mock(spec=PvConfig, max_ac_out=10000)))})
    data.data.counter_data.update({
        "counter0": Mock(spec=Counter, data=Mock(spec=CounterData, get=Mock(
            spec=CounterGet, power=6450, fault_state=0),
            config=Mock(spec=CounterConfig, is_home_consumption_counter=CounterMode.NotHomeConsumption))),
        "counter6": Mock(spec=Counter, data=Mock(spec=CounterData, get=Mock(
            spec=CounterGet, power=4300,  fault_state=0),
            config=Mock(spec=CounterConfig, is_home_consumption_counter=CounterMode.NotHomeConsumption))),
        "counter7": Mock(spec=Counter, data=Mock(spec=CounterData, get=Mock(
            spec=CounterGet, power=20700, fault_state=0),
            config=Mock(spec=CounterConfig, is_home_consumption_counter=CounterMode.NotHomeConsumption))),
        "counter13": Mock(spec=Counter, data=Mock(spec=CounterData, get=Mock(
            spec=CounterGet, power=7150, fault_state=0),
            config=Mock(spec=CounterConfig, is_home_consumption_counter=CounterMode.NotHomeConsumption))),
        "counter14": Mock(spec=Counter, data=Mock(spec=CounterData, get=Mock(
            spec=CounterGet, power=-9750, fault_state=0),
            config=Mock(spec=CounterConfig, is_home_consumption_counter=CounterMode.NotHomeConsumption))),

        "counter11": Mock(spec=Counter, data=Mock(spec=CounterData, get=Mock(
            spec=CounterGet, power=6700, fault_state=0),
            config=Mock(spec=CounterConfig, is_home_consumption_counter=CounterMode.HomeConsumption))),

        "counter8": Mock(spec=Counter, data=Mock(spec=CounterData, get=Mock(
            spec=CounterGet, power=7400, fault_state=0),
            config=Mock(spec=CounterConfig, is_home_consumption_counter=CounterMode.HomeConsumption))),
        "counter9": Mock(spec=Counter, data=Mock(spec=CounterData, get=Mock(
            spec=CounterGet,  power=4300, fault_state=0),
            config=Mock(spec=CounterConfig, is_home_consumption_counter=CounterMode.HomeConsumption))),
        "counter10": Mock(spec=Counter, data=Mock(spec=CounterData, get=Mock(
            spec=CounterGet, power=7150, fault_state=0),
            config=Mock(spec=CounterConfig, is_home_consumption_counter=CounterMode.HomeConsumption))),
        "counter15": Mock(spec=Counter, data=Mock(spec=CounterData, get=Mock(
            spec=CounterGet, power=-9750, fault_state=0),
            config=Mock(spec=CounterConfig, is_home_consumption_counter=CounterMode.HomeConsumption))),

        "counter16": Mock(spec=Counter, data=Mock(spec=CounterData, get=Mock(
            spec=CounterGet, power=4300,  fault_state=0),
            config=Mock(spec=CounterConfig, is_home_consumption_counter=CounterMode.AutoHomeConsumption))),
        "counter17": Mock(spec=Counter, data=Mock(spec=CounterData, get=Mock(
            spec=CounterGet, power=7150, fault_state=0),
            config=Mock(spec=CounterConfig, is_home_consumption_counter=CounterMode.AutoHomeConsumption))),
    })
