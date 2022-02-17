from typing import List
import pytest
from unittest.mock import Mock


from control.counter import CounterAll, get_max_id_in_hierarchy
from modules.common.component_type import ComponentType
from helpermodules.pub import PubSingleton


def hierarchy_empty() -> CounterAll:
    c = CounterAll()
    c.data["get"] = {"hierarchy": []}
    return c


def hierarchy_one_level() -> CounterAll:
    c = CounterAll()
    c.data["get"] = {"hierarchy": [{"id": 0, "type": "counter", "children": []}]}
    return c


def hierarchy_two_level() -> CounterAll:
    c = CounterAll()
    c.data["get"] = {"hierarchy": [{"id": 0, "type": "counter",
                                   "children": [{"id": 2, "type": "cp", "children": []}]}]}
    return c


class Params:
    def __init__(self, name: str,
                 counter_all: CounterAll,
                 new_id: int,
                 new_type: ComponentType,
                 id_to_find: int,
                 expected_return: bool,
                 expected_hierarchy: List) -> None:
        self.name = name
        self.counter_all = counter_all
        self.new_id = new_id
        self.new_type = new_type
        self.id_to_find = id_to_find
        self.expected_return = expected_return
        self.expected_hierarchy = expected_hierarchy


cases_add_item_aside = [
    Params("add_aside_one_level", hierarchy_one_level(), 1, ComponentType.INVERTER, 0, True, [
           {"id": 0, "type": "counter", "children": []},
           {"id": 1, "type": "inverter", "children": []}]),
    Params(
        "add_aside_two_level", hierarchy_two_level(),
        1, ComponentType.INVERTER, 0, True,
        [{'id': 0, 'type': "counter", 'children': [
            {'id': 2, 'type': "cp", 'children': []}]},
         {'id': 1, 'type': "inverter", 'children': []}])
]

cases_add_item_below = [
    Params("add_below_one_level", hierarchy_one_level(), 1, ComponentType.INVERTER, 0, True, [
           {"id": 0, "type": "counter", "children": [
               {"id": 1, "type": "inverter", "children": []}]}]),
    Params(
        "add_below_two_level", hierarchy_two_level(),
        1, ComponentType.INVERTER, 2, True,
        [{'id': 0, 'type': "counter", 'children': [
            {'id': 2, 'type': "cp", 'children': [
                {'id': 1, 'type': "inverter", 'children': []}]}]}])
]

cases_delete_keep_children = [
    Params("delete_keep_children_one_level", hierarchy_one_level(), 0, ComponentType.INVERTER, 0, True, []),
    Params(
        "delete_keep_children_two_level", hierarchy_two_level(),
        0, ComponentType.INVERTER, 0, True,
        [{'id': 2, 'type': "cp", 'children': []}])
]

cases_delete_discard_children = [
    Params("delete_discard_children_one_level", hierarchy_one_level(), 0, ComponentType.INVERTER, 0, True, []),
    Params("delete_discard_children_two_level", hierarchy_two_level(), 0, ComponentType.INVERTER, 0, True, [])
]


@pytest.fixture(autouse=True)
def set_up(monkeypatch):
    mock_init = Mock(name="init", return_value=None)
    mock_pub = Mock(name="pub")
    monkeypatch.setattr(PubSingleton, "__init__", mock_init)
    monkeypatch.setattr(PubSingleton, "pub", mock_pub)


@pytest.mark.parametrize("params", cases_add_item_aside, ids=[c.name for c in cases_add_item_aside])
def test_add_item_aside(params: Params):
    # execution
    actual = params.counter_all.hierarchy_add_item_aside(params.new_id, params.new_type, params.id_to_find)

    # evaluation
    assert actual == params.expected_return
    assert params.counter_all.data["get"]["hierarchy"] == params.expected_hierarchy


@pytest.mark.parametrize("params", cases_add_item_below, ids=[c.name for c in cases_add_item_below])
def test_add_item_below(params: Params):
    # execution
    actual = params.counter_all.hierarchy_add_item_below(params.new_id, params.new_type, params.id_to_find)

    # evaluation
    assert actual == params.expected_return
    assert params.counter_all.data["get"]["hierarchy"] == params.expected_hierarchy


@pytest.mark.parametrize("params", cases_delete_keep_children, ids=[c.name for c in cases_delete_keep_children])
def test_delete_keep_children(params: Params):
    # execution
    actual = params.counter_all.hierarchy_remove_item(params.id_to_find, True)

    # evaluation
    assert actual == params.expected_return
    assert params.counter_all.data["get"]["hierarchy"] == params.expected_hierarchy


@pytest.mark.parametrize("params", cases_delete_discard_children, ids=[c.name for c in cases_delete_discard_children])
def test_delete_discard_children(params: Params):
    # execution
    actual = params.counter_all.hierarchy_remove_item(params.id_to_find, False)

    # evaluation
    assert actual == params.expected_return
    assert params.counter_all.data["get"]["hierarchy"] == params.expected_hierarchy


def test_empty_hierarchy():
    # execution
    c = hierarchy_empty()

    # evaluation
    with pytest.raises(IndexError):
        c.hierarchy_add_item_aside(1, ComponentType.INVERTER, 0)
    with pytest.raises(IndexError):
        c.hierarchy_add_item_below(1, ComponentType.INVERTER, 0)
    with pytest.raises(IndexError):
        c.hierarchy_remove_item(0)


def test_unknown_id():
    # execution
    c = hierarchy_two_level()

    # evaluation
    with pytest.raises(ValueError):
        c.hierarchy_add_item_aside(1, ComponentType.INVERTER, 5)
    with pytest.raises(ValueError):
        c.hierarchy_add_item_below(1, ComponentType.INVERTER, 5)
    with pytest.raises(ValueError):
        c.hierarchy_remove_item(5)


def test_get_max_id():
    assert get_max_id_in_hierarchy([], -1) == -1
    assert get_max_id_in_hierarchy([{"id": 0, "type": ComponentType.COUNTER, "children": []}], -1) == 0
    assert get_max_id_in_hierarchy([{"id": 0, "type": ComponentType.COUNTER, "children": [
                                   {"id": 2, "type": ComponentType.CHARGEPOINT, "children": []}]}], -1) == 2
    assert get_max_id_in_hierarchy([{"id": 0, "type": ComponentType.COUNTER, "children": [
        {"id": 2, "type": ComponentType.CHARGEPOINT, "children": [
            {"id": 5, "type": ComponentType.CHARGEPOINT, "children": []}]},
        {"id": 6, "type": ComponentType.CHARGEPOINT, "children": []}]}], -1) == 6
