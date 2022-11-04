from typing import Dict, List, Optional, Union
import pytest


from control.counter import CounterAll, get_max_id_in_hierarchy
from modules.common.component_type import ComponentType


def hierarchy_empty() -> CounterAll:
    c = CounterAll()
    c.data.get.hierarchy = []
    return c


def hierarchy_one_level() -> CounterAll:
    c = CounterAll()
    c.data.get.hierarchy = [{"id": 0, "type": "counter", "children": []}]
    return c


def hierarchy_two_level() -> CounterAll:
    c = CounterAll()
    c.data.get.hierarchy = [{"id": 0, "type": "counter",
                             "children": [{"id": 2, "type": "cp", "children": []}]},
                            {"id": 7, "type": "inverter", "children": []}]
    return c


def hierarchy_cp() -> CounterAll:
    c = CounterAll()
    c.data.get.hierarchy = [{"id": 0, "type": "counter",
                             "children": [
                                 {"id": 7, "type": "inverter", "children": []},
                                 {"id": 2, "type": "counter", "children": [
                                           {"id": 3, "type": "cp", "children": []},
                                           {"id": 4, "type": "counter", "children": [
                                               {"id": 5, "type": "cp", "children": []},
                                               {"id": 6, "type": "cp", "children": []}]}]}]}]
    return c


class ParamsAdd:
    def __init__(self, name: str,
                 counter_all: CounterAll,
                 new_id: int,
                 new_type: ComponentType,
                 id_to_find: int,
                 expected_hierarchy: List,
                 expected_return: Optional[bool] = None) -> None:
        self.name = name
        self.counter_all = counter_all
        self.new_id = new_id
        self.new_type = new_type
        self.id_to_find = id_to_find
        self.expected_return = expected_return
        self.expected_hierarchy = expected_hierarchy


class ParamsItem:
    def __init__(self, name: str,
                 counter_all: CounterAll,
                 id,
                 expected_return: Optional[Union[List, Dict]] = None,
                 expected_hierarchy: Optional[List] = None) -> None:
        self.name = name
        self.counter_all = counter_all
        self.id = id
        self.expected_return = expected_return
        self.expected_hierarchy = expected_hierarchy


cases_add_item_below = [
    ParamsAdd("add_below_one_level", hierarchy_one_level(), 1, ComponentType.INVERTER, 0, [
        {"id": 0, "type": "counter", "children": [
            {"id": 1, "type": "inverter", "children": []}]}]),
    ParamsAdd(
        "add_below_two_level", hierarchy_two_level(),
        1, ComponentType.INVERTER, 2,
        [{'id': 0, 'type': "counter", 'children': [
            {'id': 2, 'type': "cp", 'children': [
                {'id': 1, 'type': "inverter", 'children': []}]}]},
         {"id": 7, "type": "inverter", "children": []}])
]


@pytest.mark.parametrize("params", cases_add_item_below, ids=[c.name for c in cases_add_item_below])
def test_add_item_below(params: ParamsAdd):
    # execution
    params.counter_all.hierarchy_add_item_below(params.new_id, params.new_type, params.id_to_find)

    # evaluation
    assert params.counter_all.data.get.hierarchy == params.expected_hierarchy


cases_delete_keep_children = [
    ParamsItem("delete_keep_children_one_level", hierarchy_one_level(), 0, expected_hierarchy=[]),
    ParamsItem(
        "delete_keep_children_two_level", hierarchy_two_level(), 0,
        expected_hierarchy=[{"id": 7, "type": "inverter", "children": []}, {'id': 2, 'type': "cp", 'children': []}])
]


@pytest.mark.parametrize("params", cases_delete_keep_children, ids=[c.name for c in cases_delete_keep_children])
def test_delete_keep_children(params: ParamsItem):
    # execution
    params.counter_all.hierarchy_remove_item(params.id, True)

    # evaluation
    assert params.counter_all.data.get.hierarchy == params.expected_hierarchy


cases_delete_discard_children = [
    ParamsItem("delete_discard_children_one_level", hierarchy_one_level(),  0, expected_hierarchy=[]),
    ParamsItem("delete_discard_children_two_level", hierarchy_two_level(),
               0, expected_hierarchy=[{"id": 7, "type": "inverter", "children": []}])
]


@pytest.mark.parametrize("params", cases_delete_discard_children, ids=[c.name for c in cases_delete_discard_children])
def test_delete_discard_children(params: ParamsItem):
    # execution
    params.counter_all.hierarchy_remove_item(params.id, False)

    # evaluation
    assert params.counter_all.data.get.hierarchy == params.expected_hierarchy


cases_get_chargepoints_of_counter = [
    ParamsItem("get_chargepoints_of_counter", hierarchy_cp(), "counter2", expected_return=["cp3", "cp5", "cp6"]),
    ParamsItem("get_chargepoints_of_counter", hierarchy_two_level(), "counter0", expected_return=["cp2"])
]


@pytest.mark.parametrize("params",
                         cases_get_chargepoints_of_counter,
                         ids=[c.name for c in cases_get_chargepoints_of_counter])
def test_get_chargepoints_of_counter(params: ParamsItem):
    # execution
    actual = params.counter_all.get_chargepoints_of_counter(params.id)

    # evaluation
    assert actual == params.expected_return


cases_get_counters_to_check = [
    ParamsItem("get_counters_to_check", hierarchy_cp(), 5, expected_return=["counter4", "counter2", "counter0"]),
    ParamsItem("get_counters_to_check", hierarchy_two_level(), 2, expected_return=["counter0"])
]


@pytest.mark.parametrize("params", cases_get_counters_to_check, ids=[c.name for c in cases_get_counters_to_check])
def test_get_counters_to_check(params: ParamsItem):
    # execution
    actual = params.counter_all.get_counters_to_check(params.id)

    # evaluation
    assert actual == params.expected_return


cases_get_entry_of_element = [
    ParamsItem("get_entry_of_element", hierarchy_cp(), 5, expected_return={"id": 5, "type": "cp", "children": []}),
    ParamsItem("get_entry_of_element", hierarchy_two_level(), 0,
               expected_return={"id": 0, "type": "counter",
                                "children": [
                                    {"id": 2, "type": "cp", "children": []}]})
]


@pytest.mark.parametrize("params", cases_get_entry_of_element, ids=[c.name for c in cases_get_entry_of_element])
def test_get_entry_of_element(params: ParamsItem):
    # execution
    actual = params.counter_all.get_entry_of_element(params.id)

    # evaluation
    assert actual == params.expected_return


cases_get_entry_of_parent = [
    ParamsItem("get_entry_of_parent_cp", hierarchy_cp(), 5, expected_return={"id": 4, "type": "counter", "children": [
        {"id": 5, "type": "cp", "children": []},
        {"id": 6, "type": "cp", "children": []}]}),
    ParamsItem("get_entry_of_parent_two_level", hierarchy_two_level(), 2, expected_return={"id": 0, "type": "counter",
                                                                                           "children": [
                                                                                               {"id": 2,
                                                                                                   "type": "cp",
                                                                                                   "children": []}]}),
    ParamsItem("get_entry_of_parent_one_level", hierarchy_one_level(), 0, expected_return={})
]


@pytest.mark.parametrize("params", cases_get_entry_of_parent, ids=[c.name for c in cases_get_entry_of_parent])
def test_get_entry_of_parent(params: ParamsItem):
    # execution
    actual = params.counter_all.get_entry_of_parent(params.id)

    # evaluation
    assert actual == params.expected_return


def test_empty_hierarchy():
    # execution
    c = hierarchy_empty()

    # evaluation
    with pytest.raises(IndexError):
        c.hierarchy_add_item_below(1, ComponentType.INVERTER, 0)
    with pytest.raises(IndexError):
        c.hierarchy_remove_item(0)


def test_unknown_id():
    # execution
    c = hierarchy_two_level()

    # evaluation
    with pytest.raises(IndexError):
        c.hierarchy_add_item_below(1, ComponentType.INVERTER, 5)
    with pytest.raises(IndexError):
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


cases_get_all_elements_without_children = [
    ParamsItem("get_all_elements_without_children_cp", hierarchy_cp(),
               0, expected_return=[{"id": 7, "type": "inverter", "children": []},
               {"id": 3, "type": "cp", "children": []}, {"id": 5, "type": "cp", "children": []},
               {"id": 6, "type": "cp", "children": []}]),
    ParamsItem("get_all_elements_without_children_two_level", hierarchy_two_level(),
               0, expected_return=[{"id": 2, "type": "cp", "children": []}]),
    ParamsItem("get_all_elements_without_children_one_level", hierarchy_one_level(), 0, expected_return=[])
]


@pytest.mark.parametrize("params",
                         cases_get_all_elements_without_children,
                         ids=[c.name for c in cases_get_all_elements_without_children])
def test_get_all_elements_without_children(params: ParamsItem):
    # execution
    actual = params.counter_all.get_all_elements_without_children(params.id)

    # evaluation
    assert actual == params.expected_return


cases_list_of_elements_per_level = [
    ParamsItem("list_of_elements_per_level_cp", hierarchy_cp(),
               0, expected_return=[[{"id": 0, "type": "counter"}],
                                   [{"id": 7, "type": "inverter"}, {"id": 2, "type": "counter"}],
                                   [{"id": 3, "type": "cp"}, {"id": 4, "type": "counter"}],
                                   [{"id": 5, "type": "cp"}, {"id": 6, "type": "cp"}]]),
    ParamsItem("list_of_elements_per_level_two_level", hierarchy_two_level(),
               0, expected_return=[[{"id": 0, "type": "counter"}, {"id": 7, "type": "inverter"}],
                                   [{"id": 2, "type": "cp"}]]),
    ParamsItem("list_of_elements_per_level_one_level", hierarchy_one_level(),
               0, expected_return=[[{"id": 0, "type": "counter"}]])
]


@pytest.mark.parametrize("params",
                         cases_list_of_elements_per_level,
                         ids=[c.name for c in cases_list_of_elements_per_level])
def test_list_of_elements_per_level(params: ParamsItem):
    # execution
    actual = params.counter_all.get_list_of_elements_per_level()

    # evaluation
    assert actual == params.expected_return
