from typing import Callable
from unittest.mock import Mock
import pytest

from control import data
from control.conftest import hierarchy_standard, hierarchy_hybrid, hierarchy_nested
from control.counter_all import CounterAll
from modules.common.fault_state import FaultStateLevel


@pytest.mark.parametrize("counter_all",
                         [pytest.param(hierarchy_standard, id="standard"),
                          pytest.param(hierarchy_hybrid, id="hybrid"),
                             pytest.param(hierarchy_nested, id="nested")])
def test_calc_home_consumption(counter_all: Callable[[], CounterAll], data_):
    #
    c = counter_all()

    # execution
    home_consumption = c._calc_home_consumption()[0]

    # evaluation
    assert home_consumption == 500


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
