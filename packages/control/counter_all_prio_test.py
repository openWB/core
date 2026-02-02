from dataclasses import dataclass
from unittest.mock import Mock

import pytest
from control import data
from control.chargepoint.chargepoint import Chargepoint
from control.counter_all import CounterAll
from control.ev.ev import Ev


@pytest.fixture()
def mock_data() -> None:
    data.data_init(Mock())


@dataclass
class EvFullPowerState:
    ev0_full_power: bool = False
    ev1_full_power: bool = False
    ev2_full_power: bool = False
    ev3_full_power: bool = False
    ev4_full_power: bool = False


PRIO_LIST_FLASH_END = [{"type": "vehicle", "id": 0},
                       {"type": "vehicle", "id": 1},
                       {"type": "vehicle", "id": 2},
                       {"type": "vehicle", "id": 4}]
PRIO_LIST_FLASH_START = [{"type": "vehicle", "id": 0},
                         {"type": "vehicle", "id": 3},
                         {"type": "vehicle", "id": 2}]
PRIO_LIST_DOUBLE_FLASH_START = [{"type": "vehicle", "id": 0},
                                {"type": "vehicle", "id": 1},
                                {"type": "vehicle", "id": 3},
                                {"type": "vehicle", "id": 2}]
PRIO_LIST_DOUBLE_FLASH_MIDDLE = [{"type": "vehicle", "id": 4},
                                 {"type": "vehicle", "id": 0},
                                 {"type": "vehicle", "id": 1},
                                 {"type": "vehicle", "id": 3},
                                 {"type": "vehicle", "id": 2}]
PRIO_LIST_DOUBLE_FLASH_END = [{"type": "vehicle", "id": 4},
                              {"type": "vehicle", "id": 0},
                              {"type": "vehicle", "id": 1}]
PRIO_LIST_NO_FLASH_END = [{"type": "vehicle", "id": 4},
                          {"type": "vehicle", "id": 1}]
PRIO_LIST_NO_FLASH_MIDDLE = [{"type": "vehicle", "id": 2},
                             {"type": "vehicle", "id": 4},
                             {"type": "vehicle", "id": 1}]
GROUPED_PAYLOAD_FLASH_MIDDLE = [
    {'items': [{'type': 'vehicle', 'id': 0}, {'type': 'vehicle', 'id': 1}], 'is_full_power_group': False},
    {'items': [{'type': 'vehicle', 'id': 2}], 'is_full_power_group': True},
    {'items': [{'type': 'vehicle', 'id': 4}], 'is_full_power_group': False}]
GROUPED_PAYLOAD_FLASH_START = [
    {'items': [{'type': 'vehicle', 'id': 0}], 'is_full_power_group': True},
    {'items': [{'type': 'vehicle', 'id': 3}, {'type': 'vehicle', 'id': 2}], 'is_full_power_group': False}]
GROUPED_PAYLOAD_DOUBLE_FLASH_START = [
    {'items': [{'type': 'vehicle', 'id': 0}], 'is_full_power_group': True},
    {'items': [{'type': 'vehicle', 'id': 1}], 'is_full_power_group': True},
    {'items': [{'type': 'vehicle', 'id': 3}, {'type': 'vehicle', 'id': 2}], 'is_full_power_group': False}]
GROUPED_PAYLOAD_DOUBLE_FLASH_MIDDLE = [
    {'items': [{'type': 'vehicle', 'id': 4}], 'is_full_power_group': False},
    {'items': [{'type': 'vehicle', 'id': 0}], 'is_full_power_group': True},
    {'items': [{'type': 'vehicle', 'id': 1}], 'is_full_power_group': True},
    {'items': [{'type': 'vehicle', 'id': 3}, {'type': 'vehicle', 'id': 2}], 'is_full_power_group': False}]
GROUPED_PAYLOAD_DOUBLE_FLASH_END = [
    {'items': [{'type': 'vehicle', 'id': 4}], 'is_full_power_group': False},
    {'items': [{'type': 'vehicle', 'id': 0}], 'is_full_power_group': True},
    {'items': [{'type': 'vehicle', 'id': 1}], 'is_full_power_group': True}]
GROUPED_PAYLOAD_FLASH_END = [
    {'items': [{'type': 'vehicle', 'id': 4}], 'is_full_power_group': False},
    {'items': [{'type': 'vehicle', 'id': 1}], 'is_full_power_group': True}]
GROUPED_PAYLOAD_NO_FLASH_MIDDLE = [
    {'items': [{'type': 'vehicle', 'id': 2}], 'is_full_power_group': True},
    {'items': [{'type': 'vehicle', 'id': 4}], 'is_full_power_group': False},
    {'items': [{'type': 'vehicle', 'id': 1}], 'is_full_power_group': True}]


@pytest.mark.parametrize("loadmanagement_prios, ev_full_power_state, expected_grouped_payload", [
    pytest.param(PRIO_LIST_FLASH_END, EvFullPowerState(ev2_full_power=True), GROUPED_PAYLOAD_FLASH_MIDDLE,),
    pytest.param(PRIO_LIST_FLASH_START, EvFullPowerState(ev0_full_power=True), GROUPED_PAYLOAD_FLASH_START,),
    pytest.param(PRIO_LIST_DOUBLE_FLASH_START, EvFullPowerState(ev0_full_power=True, ev1_full_power=True),
                 GROUPED_PAYLOAD_DOUBLE_FLASH_START,),
    pytest.param(PRIO_LIST_DOUBLE_FLASH_MIDDLE, EvFullPowerState(ev0_full_power=True, ev1_full_power=True),
                 GROUPED_PAYLOAD_DOUBLE_FLASH_MIDDLE,),
    pytest.param(PRIO_LIST_DOUBLE_FLASH_END, EvFullPowerState(ev0_full_power=True, ev1_full_power=True),
                 GROUPED_PAYLOAD_DOUBLE_FLASH_END,),
    pytest.param(PRIO_LIST_NO_FLASH_END, EvFullPowerState(ev1_full_power=True), GROUPED_PAYLOAD_FLASH_END,),
    pytest.param(PRIO_LIST_NO_FLASH_MIDDLE, EvFullPowerState(ev2_full_power=True, ev1_full_power=True),
                 GROUPED_PAYLOAD_NO_FLASH_MIDDLE,),
]
)
def test_get_prio_groups(loadmanagement_prios,
                         ev_full_power_state: EvFullPowerState,
                         expected_grouped_payload,
                         mock_data):
    # setup
    c = CounterAll()
    c.data.get.loadmanagement_prios = loadmanagement_prios
    for i in range(5):
        data.data.ev_data[f"ev{i}"] = Ev(i)
        data.data.ev_data[f"ev{i}"].data.full_power = getattr(ev_full_power_state, f"ev{i}_full_power")

    # execution
    prio_groups = c._get_prio_groups()

    # verification
    assert prio_groups == expected_grouped_payload


@pytest.mark.parametrize("prio_groups, expected_groups", [
    pytest.param(GROUPED_PAYLOAD_FLASH_MIDDLE, [([0, 1], [2]), ([4], None)]),
    pytest.param(GROUPED_PAYLOAD_FLASH_START, [(None, [0]), ([3, 2], None)]),
    pytest.param(GROUPED_PAYLOAD_DOUBLE_FLASH_START, [(None, [0]), (None, [1]), ([3, 2], None)]),
    pytest.param(GROUPED_PAYLOAD_DOUBLE_FLASH_MIDDLE, [([4], [0]), (None, [1]), ([3, 2], None)]),
    pytest.param(GROUPED_PAYLOAD_DOUBLE_FLASH_END, [([4], [0]), (None, [1])]),
    pytest.param(GROUPED_PAYLOAD_FLASH_END, [([4], [1])]),
    pytest.param(GROUPED_PAYLOAD_NO_FLASH_MIDDLE, [(None, [2]), ([4], [1])]),
]
)
def test_prio_groups_generator(prio_groups, expected_groups, mock_data, monkeypatch):
    # setup
    c = CounterAll()
    for i in range(5):
        data.data.ev_data[f"ev{i}"] = Ev(i)
    for i in range(5):
        data.data.cp_data[f"cp{i}"] = Chargepoint(i, None)
        data.data.cp_data[f"cp{i}"].data.config.ev = i

    mock_get_prio_groups = Mock(return_value=prio_groups)
    monkeypatch.setattr(CounterAll, "_get_prio_groups", mock_get_prio_groups)

    # execution
    gen = c.prio_groups_generator()

    # verification
    for t in expected_groups:
        generated = next(gen)
        if t[0] is None:
            assert generated[0] is None
        else:
            assert [cp.num for cp in generated[0]] == t[0]
        if t[1] is None:
            assert generated[1] is None
        else:
            assert [cp.num for cp in generated[1]] == t[1]
