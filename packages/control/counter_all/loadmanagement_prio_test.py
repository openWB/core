
from typing import Dict, List

import pytest

from control.chargepoint.chargepoint import Chargepoint
from control.counter_all.counter_all import CounterAll


@pytest.fixture
def cp1():
    cp = Chargepoint(1, None)
    cp.data.control_parameter.required_current = 8
    return cp


@pytest.fixture
def cp2():
    cp = Chargepoint(2, None)
    cp.data.control_parameter.required_current = 7
    return cp


@pytest.fixture
def cp3():
    cp = Chargepoint(3, None)
    cp.data.control_parameter.required_current = 6
    return cp


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


def test_sort_cps_by_loadmanagement_prios_nested_same_vehicle(cp1, cp2, cp3):
    """Alle LP haben das gleiche Fahrzeug zugeordnet"""
    # setup
    cp1.data.config.ev = 0
    cp2.data.config.ev = 0
    cp3.data.config.ev = 0

    c = CounterAll()
    c.data.get.loadmanagement_prios = [{"type": "vehicle", "id": 2}, {"type": "vehicle", "id": 0}]

    # execution
    result = c.sort_cps_by_loadmanagement_prios_nested([cp1, cp2, cp3])

    # assert - eine Gruppe mit allen CPs (sortiert nach required_current)
    assert len(result) == 1
    assert result[0] == [cp3, cp2, cp1]  # direkte Objektvergleiche!


def test_sort_cps_by_loadmanagement_prios_nested_different_vehicles(cp1, cp2, cp3):
    """Alle LP haben unterschiedliche Fahrzeuge"""
    # setup
    cp1.data.config.ev = 1
    cp2.data.config.ev = 2
    cp3.data.config.ev = 3

    c = CounterAll()
    c.data.get.loadmanagement_prios = [
        {"type": "vehicle", "id": 3},
        {"type": "vehicle", "id": 1},
        {"type": "vehicle", "id": 2}
    ]

    # execution
    result = c.sort_cps_by_loadmanagement_prios_nested([cp1, cp2, cp3])

    # assert - drei separate Gruppen
    assert len(result) == 3
    assert result[0] == [cp3]  # vehicle id=3
    assert result[1] == [cp1]  # vehicle id=1
    assert result[2] == [cp2]  # vehicle id=2


def test_sort_cps_by_loadmanagement_prios_nested_with_group(cp1, cp2, cp3):
    """LP mit unterschiedlichen Fahrzeugen, einige in Gruppe"""
    # setup
    cp1.data.config.ev = 1
    cp2.data.config.ev = 2
    cp3.data.config.ev = 3

    c = CounterAll()
    c.data.get.loadmanagement_prios = [
        {"type": "vehicle", "id": 3},
        {
            "type": "group",
            "label": "Wichtige Fahrzeuge",
            "children": [
                {"type": "vehicle", "id": 1},
                {"type": "vehicle", "id": 2}
            ]
        }
    ]

    # execution
    result = c.sort_cps_by_loadmanagement_prios_nested([cp1, cp2, cp3])

    # assert - zwei Gruppen
    assert len(result) == 2
    assert result[0] == [cp3]        # vehicle id=3 einzeln
    assert result[1] == [cp1, cp2]   # vehicles id=1,2 in der Gruppe
