from typing import List
from unittest.mock import Mock

import pytest

from control import loadmanagement
from control.counter import Counter
from control.loadmanagement import LimitingValue, Loadmanagement

COUNTER_NAME = "test counter"


@pytest.mark.parametrize(
    "available_currents, raw_power_left, expected_currents",
    [
        pytest.param([5, 10, 15], 6900, ([5, 10, 15], None)),
        pytest.param([5, 10, 25], 1000, ([0.5434782608695652, 1.0869565217391304,
                     2.717391304347826], LimitingValue.POWER.value.format(COUNTER_NAME))),
        pytest.param([5, 10, 25], 5000, ([2.717391304347826, 5.434782608695652,
                     13.58695652173913], LimitingValue.POWER.value.format(COUNTER_NAME))),
    ])
def test_limit_by_power(available_currents: List[float],
                        raw_power_left: float,
                        expected_currents: List[float],
                        monkeypatch):
    # setup
    counter_name_mock = Mock(return_value=COUNTER_NAME)
    monkeypatch.setattr(loadmanagement, "get_component_name_by_id", counter_name_mock)
    # evaluation
    currents = Loadmanagement()._limit_by_power(Counter(0), available_currents, raw_power_left, None)

    # assertion
    assert currents == expected_currents


@pytest.mark.parametrize(
    "missing_currents, raw_currents_left, expected_currents",
    [
        pytest.param([5, 10, 15], [20]*3, ([5, 10, 15], None)),
        pytest.param([5, 10, 15], [5, 8, 5], ([5, 8, 5], LimitingValue.CURRENT.value.format(COUNTER_NAME))),
    ])
def test_limit_by_current(
        missing_currents: List[float], raw_currents_left: List[float], expected_currents: List[float], monkeypatch):
    # setup
    counter_name_mock = Mock(return_value=COUNTER_NAME)
    monkeypatch.setattr(loadmanagement, "get_component_name_by_id", counter_name_mock)
    # evaluation
    currents = Loadmanagement()._limit_by_current(Counter(0), missing_currents, raw_currents_left)

    # assertion
    assert currents == expected_currents
