
from typing import Dict, List

import pytest

from control.chargepoint.chargepoint import Chargepoint
from control.counter_all.counter_all import CounterAll


@pytest.mark.parametrize(
    "loadmanagement_prios, id, type, expected_loadmanagement_prios",
    [
        pytest.param([], 2, "vehicle", [{"type": "vehicle", "id": 2}], id="emtpy list"),
        pytest.param([{"type": "vehicle", "id": 3}], 2, "vehicle", [{"type": "vehicle", "id": 3},
                                                                    {"type": "vehicle", "id": 2}], id="flat list"),
        pytest.param([
            {
                "type": "group",
                "label": "Wichtige Fahrzeuge",
                "children": [
                        {"type": "vehicle", "id": 0, },
                        {"type": "vehicle", "id": 1, },
                ]
            },
            {"type": "vehicle", "id": 2},
        ], 4, "vehicle", [
            {
                "type": "group",
                "label": "Wichtige Fahrzeuge",
                "children": [
                        {"type": "vehicle", "id": 0, },
                        {"type": "vehicle", "id": 1, },
                ]
            },
            {"type": "vehicle", "id": 2},
            {"type": "vehicle", "id": 4},
        ], id="nested list"),
    ]
)
def test_add_item(loadmanagement_prios: List[Dict], id: int, type: str, expected_loadmanagement_prios: List[Dict]):
    # setup
    c = CounterAll()
    c.data.get.loadmanagement_prios = loadmanagement_prios

    # execution
    c.add_loadmanagement_prio_item(type, id)

    # assert
    assert c.data.get.loadmanagement_prios == expected_loadmanagement_prios


@pytest.mark.parametrize(
    "loadmanagement_prios, id, type, expected_loadmanagement_prios",
    [
        pytest.param([{"type": "vehicle", "id": 3}, {"type": "vehicle", "id": 2}],
                     2, "vehicle", [{"type": "vehicle", "id": 3}], id="flat list"),
        pytest.param([
            {
                "type": "group",
                "label": "Wichtige Fahrzeuge",
                "children": [
                        {"type": "vehicle", "id": 0, },
                        {"type": "vehicle", "id": 1, },
                ]
            },
            {"type": "vehicle", "id": 2},
        ], 2, "vehicle", [
            {
                "type": "group",
                "label": "Wichtige Fahrzeuge",
                "children": [
                        {"type": "vehicle", "id": 0, },
                        {"type": "vehicle", "id": 1, },
                ]
            },
        ], id="nested list"),
        pytest.param([
            {
                "type": "group",
                        "label": "Wichtige Fahrzeuge",
                        "children": [
                            {"type": "vehicle", "id": 0, },
                            {"type": "vehicle", "id": 1, },
                        ]
            },
            {"type": "vehicle", "id": 2},
        ], 0, "vehicle", [
            {
                "type": "group",
                "label": "Wichtige Fahrzeuge",
                "children": [
                        {"type": "vehicle", "id": 1, },
                ]
            },
            {"type": "vehicle", "id": 2},
        ], id="nested list, remove from group"),
        pytest.param([
            {
                "type": "group",
                        "label": "Wichtige Fahrzeuge",
                        "children": [
                            {"type": "vehicle", "id": 0, },
                        ]
            },
            {"type": "vehicle", "id": 2},
        ], 0, "vehicle", [{"type": "vehicle", "id": 2}], id="nested list, empty group"),
    ]
)
def test_remove_loadmanagement_prio_item(loadmanagement_prios: List[Dict],
                                         id: int,
                                         type: str,
                                         expected_loadmanagement_prios: List[Dict]):
    # setup
    c = CounterAll()
    c.data.get.loadmanagement_prios = loadmanagement_prios

    # execution
    c.remove_loadmanagement_prio_item(id)

    # assert
    assert c.data.get.loadmanagement_prios == expected_loadmanagement_prios


@pytest.mark.parametrize(
    "config_ev_list, loadmanagement_prios, sorted_cp_ids",
    [
        pytest.param([0]*3,
                     [{"type": "vehicle", "id": 2}, {"type": "vehicle", "id": 0}],
                     [1, 2, 3],
                     id="alle LP haben das gleiche Fahrzeug zugeordnet"),
        pytest.param([1, 2, 3],
                     [{"type": "vehicle", "id": 3}, {"type": "vehicle", "id": 1}, {"type": "vehicle", "id": 0}],
                     [3, 1, 2],
                     id="alle LP haben unterschiedliche Fahrzeuge"),
        pytest.param([1, 2, 3],
                     [{"type": "vehicle", "id": 3}, {
                      "type": "group",
                      "label": "Wichtige Fahrzeuge",
                      "children": [{"type": "vehicle", "id": 1}, {
                          "type": "vehicle", "id": 2}]}],
                     [3, 1, 2],
                     id="alle LP haben unterschiedliche Fahrzeuge mit Gruppe"),
    ]
)
def test_sort_cps_by_loadmanagement_prios_flat(config_ev_list: List[int],
                                               loadmanagement_prios: List[Dict],
                                               sorted_cp_ids: List[int]):
    # setup
    cp1 = Chargepoint(1, None)
    cp1.data.config.ev = config_ev_list[0]
    cp2 = Chargepoint(2, None)
    cp2.data.config.ev = config_ev_list[1]
    cp3 = Chargepoint(3, None)
    cp3.data.config.ev = config_ev_list[2]

    c = CounterAll()
    c.data.get.loadmanagement_prios = loadmanagement_prios

    # execution
    sorted_cps = c.sort_cps_by_loadmanagement_prios_flat([cp1, cp2, cp3])

    # assert
    for i, cp in enumerate(sorted_cps):
        assert cp.num == sorted_cp_ids[i]


def test_sort_cps_by_loadmanagement_prios_nested():
    # setup
    cp1 = Chargepoint(1, None)
    cp1.data.config.ev = 1
    cp2 = Chargepoint(2, None)
    cp2.data.config.ev = 2
    cp3 = Chargepoint(3, None)
    cp3.data.config.ev = 3

    c = CounterAll()
    c.data.get.loadmanagement_prios = [{"type": "vehicle", "id": 3}, {
        "type": "group",
        "label": "Wichtige Fahrzeuge",
        "children": [{"type": "vehicle", "id": 1}, {
            "type": "vehicle", "id": 2}]}]

    # execution
    sorted_cps = c.sort_cps_by_loadmanagement_prios_nested([cp1, cp2, cp3])

    # assert
    assert sorted_cps == [[cp3], [cp1, cp2]]
