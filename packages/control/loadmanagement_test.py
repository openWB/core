from typing import List

import pytest

from control.loadmanagement import LimitingValue, Loadmanagement


@pytest.mark.parametrize(
    "available_currents, raw_power_left, expected_currents",
    [
        pytest.param([5, 10, 15], 6900, ([5, 10, 15], None)),
        pytest.param([5, 10, 25], 1000, ([0.5434782608695652, 1.0869565217391304,
                     2.717391304347826], LimitingValue.POWER)),
        pytest.param([5, 10, 25], 5000, ([2.717391304347826, 5.434782608695652,
                     13.58695652173913], LimitingValue.POWER)),
    ])
def test_limit_by_power(available_currents: List[float], raw_power_left: float, expected_currents: List[float]):
    # setup & evaluation
    currents = Loadmanagement()._limit_by_power(available_currents, raw_power_left, None)

    # assertion
    assert currents == expected_currents


@pytest.mark.parametrize(
    "missing_currents, raw_currents_left, expected_currents",
    [
        pytest.param([5, 10, 15], [20]*3, ([5, 10, 15], None)),
        pytest.param([5, 10, 15], [5, 8, 5], ([5, 8, 5], LimitingValue.CURRENT)),
    ])
def test_limit_by_current(
        missing_currents: List[float], raw_currents_left: List[float], expected_currents: List[float]):
    # setup & evaluation
    currents = Loadmanagement()._limit_by_current(missing_currents, raw_currents_left)

    # assertion
    assert currents == expected_currents
