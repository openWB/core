from typing import Dict, List, Optional, Tuple, Union
from unittest.mock import Mock

import pytest

from control import data
from control.algorithm import filter_chargepoints
from control.chargemode import Chargemode
from control.chargepoint.chargepoint import Chargepoint
from control.consumer.consumer import Consumer
from control.counter_all.counter_all import CounterAll
from control.load_protocol import Load


@pytest.fixture(autouse=True)
def mock_data() -> None:
    data.data_init(Mock())


@pytest.fixture(autouse=True)
def mock_cp1() -> Chargepoint:
    return Chargepoint(1, None)


@pytest.fixture(autouse=True)
def mock_cp2() -> Chargepoint:
    return Chargepoint(2, None)


@pytest.fixture(autouse=True)
def mock_consumer3() -> Consumer:
    return Consumer(3)


# flache prio liste
# prio liste mit gruppe und einzel lp und verbraucher
# ein lademodus
# zwei lademodi
# ein fahrzeug für mwhrere ladepunkte
# required current 0 für ein fahrzeug

@pytest.mark.parametrize(
    "required_current_1, ev_1, chargemode_filter, loadmanagement_prios, expected_cp_indices",
    [
        pytest.param(6, 1, ((Chargemode.SCHEDULED_CHARGING, Chargemode.INSTANT_CHARGING),),
                     [{"type": "vehicle", "id": 1},
                      {"type": "vehicle", "id": 2},
                      {"type": "consumer", "id": 3}],
                     [1, 3], id="flat prio list"),
        pytest.param(6, 1, ((Chargemode.SCHEDULED_CHARGING, Chargemode.INSTANT_CHARGING),),
                     [{"type": "vehicle", "id": 1},
                      {
                         "type": "group",
                         "label": "Gruppe 1",
                         "children": [
                             {"type": "vehicle", "id": 2},
                             {"type": "consumer", "id": 3}]}],
                     [1, 3], id="grouped prio list"),
        pytest.param(6, 2, ((Chargemode.SCHEDULED_CHARGING, Chargemode.INSTANT_CHARGING),
                            (Chargemode.INSTANT_CHARGING, Chargemode.INSTANT_CHARGING)),
                     [{"type": "vehicle", "id": 1},
                      {"type": "consumer", "id": 3},
                      {"type": "vehicle", "id": 2}],
                     [3, 1, 2], id="ev 2 for cp 1 and cp 2"),
        pytest.param(0, 1, ((Chargemode.SCHEDULED_CHARGING, Chargemode.INSTANT_CHARGING),
                            (Chargemode.INSTANT_CHARGING, Chargemode.INSTANT_CHARGING)),
                     [{"type": "vehicle", "id": 1},
                      {"type": "consumer", "id": 3},
                      {"type": "vehicle", "id": 2}],
                     [3, 2], id="required current 0 for cp 1"),
    ])
def test_get_loadmanagement_prios(
        required_current_1: int,
        ev_1: int,
        chargemode_filter: Tuple[Tuple[Optional[Chargemode], Chargemode]],
        loadmanagement_prios: List[Dict[str, Union[str, int, List[Dict[str, Union[str, int]]]]]],
        expected_cp_indices: List[int],
        mock_cp1: Chargepoint,
        mock_cp2: Chargepoint,
        mock_consumer3: Consumer):
    # setup
    data.data.cp_data = {"cp1": mock_cp1, "cp2": mock_cp2}
    data.data.cp_data["cp1"].data.config.ev = ev_1
    data.data.cp_data["cp1"].data.control_parameter.required_current = required_current_1
    data.data.cp_data["cp1"].data.control_parameter.chargemode = Chargemode.SCHEDULED_CHARGING
    data.data.cp_data["cp1"].data.control_parameter.submode = Chargemode.INSTANT_CHARGING

    data.data.cp_data["cp2"].data.config.ev = 2
    data.data.cp_data["cp2"].data.control_parameter.required_current = 6
    data.data.cp_data["cp2"].data.control_parameter.chargemode = Chargemode.INSTANT_CHARGING
    data.data.cp_data["cp2"].data.control_parameter.submode = Chargemode.INSTANT_CHARGING

    data.data.consumer_data = {"consumer3": mock_consumer3}
    data.data.consumer_data["consumer3"].data.control_parameter.required_current = 1
    data.data.consumer_data["consumer3"].data.control_parameter.chargemode = Chargemode.SCHEDULED_CHARGING
    data.data.consumer_data["consumer3"].data.control_parameter.submode = Chargemode.INSTANT_CHARGING

    data.data.counter_all_data = CounterAll()
    data.data.counter_all_data.data.get.loadmanagement_prios = loadmanagement_prios

    # evaluation
    valid_loads = filter_chargepoints.get_loads_by_chargemodes(chargemode_filter)

    # assertion
    load_mapping: Dict[int, Load] = {1: mock_cp1, 2: mock_cp2, 3: mock_consumer3}
    expected_valid_loads = [load_mapping[i] for i in expected_cp_indices]
    assert valid_loads == expected_valid_loads
