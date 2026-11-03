import pytest

from control.algorithm.utils import get_medium_charging_current


@pytest.mark.parametrize(
    "currents, expected_current",
    [
        ([0.25, 0, 0], 0),
        ([0.5, 0, 0], 0.5),
        ([0.25, 0.75, 0], 0.75),
        ([6, 8, 0], 7),
        ([0, 0, 0], 0),
    ],
)
def test_charging_current_keeps_default_chargepoint_threshold(currents, expected_current):
    assert get_medium_charging_current(currents) == pytest.approx(expected_current)
