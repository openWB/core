from typing import List
from unittest.mock import Mock
import pytest

from control import data
from control.conftest import hierarchy_hybrid, hierarchy_nested, hierarchy_standard
from control.counter import Counter
from control.general import General
from modules.common.fault_state import FaultStateLevel


@pytest.fixture
def general_data_fixture() -> None:
    data.data_init(Mock())
    data.data.general_data = General()


@pytest.mark.parametrize("fault_state, expected_loadmanagement_available",
                         [pytest.param(FaultStateLevel.ERROR, False),
                          pytest.param(FaultStateLevel.NO_ERROR, True)])
def test_set_loadmanagement_state(fault_state: FaultStateLevel,
                                  expected_loadmanagement_available: bool,
                                  monkeypatch,
                                  data_):
    # setup
    connected_cps_mock = Mock(return_value=["cp3", "cp4"])
    monkeypatch.setattr(data.data.counter_all_data, "get_chargepoints_of_counter", connected_cps_mock)
    counter = Counter(0)
    counter.data["get"]["fault_state"] = fault_state

    # execution
    counter._set_loadmanagement_state()

    # evaluation
    assert data.data.cp_data["cp3"].data.set.loadmanagement_available == expected_loadmanagement_available
    assert data.data.cp_data["cp4"].data.set.loadmanagement_available == expected_loadmanagement_available


@pytest.mark.parametrize("raw_currents_left, expected_max_exceeding",
                         [pytest.param([32, 32, 15], [0]*3, id="unbalanced load limit not exceeded"),
                          pytest.param([32, 35, 15], [0]*3, id="unbalanced load limit not exceeded with export"),
                          pytest.param([32, 55, 33], [0]*3,
                                       id="unbalanced load limit not exceeded with export two phases"),
                          pytest.param([32, 32, 13], [0, 0, 2], id="unbalanced load limit exceeded on one phase"),
                          pytest.param([29, 11, 8], [0, 1, 4], id="unbalanced load limit exceeded on two phases"),
                          pytest.param([35, 11, 8], [0, 4, 7],
                          id="unbalanced load limit exceeded on two phases with export")])
def test_get_unbalanced_load_exceeding(raw_currents_left: List[float],
                                       expected_max_exceeding: List[float],
                                       monkeypatch,
                                       general_data_fixture):
    # setup
    get_evu_counter_mock = Mock(return_value="counter0")
    monkeypatch.setattr(data.data.counter_all_data, "get_evu_counter_str", get_evu_counter_mock)
    counter = Counter(0)
    counter.data.update({"config": {"max_currents": [32]*3}})
    data.data.general_data.data.chargemode_config.unbalanced_load = True

    # execution
    max_exceeding = counter.get_unbalanced_load_exceeding(raw_currents_left)

    # evaluation
    assert max_exceeding == expected_max_exceeding


@pytest.mark.parametrize("hierarchy, max_currents, expected_raw_currents_left",
                         [pytest.param(hierarchy_standard, [40]*3, [39, 0, 9], id="Überbelastung"),
                          (hierarchy_standard, [60]*3, [59, 14, 29]),
                          (hierarchy_hybrid, [60]*3, [59, 14, 29]),
                          (hierarchy_nested, [60]*3, [59, 14, 29])])
def test_set_current_left(hierarchy,
                          max_currents: List[float],
                          expected_raw_currents_left: List[float],
                          monkeypatch,
                          data_):
    # setup
    get_entry_of_element_mock = Mock(return_value=hierarchy().data.get.hierarchy[0])
    monkeypatch.setattr(data.data.counter_all_data, "get_entry_of_element", get_entry_of_element_mock)
    counter = Counter(0)
    counter.data.update({"config": {"max_currents": max_currents}, "get": {"currents": [55]*3}})

    # execution
    counter._set_current_left()

    # evaluation
    assert counter.data["set"]["raw_currents_left"] == expected_raw_currents_left
