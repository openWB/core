import pytest

from control.chargepoint.chargepoint import Chargepoint
from control.consumer.consumer import Consumer


@pytest.mark.parametrize(
    "currents, expected_consumer, expected_chargepoint",
    [
        ([0, 0, 0], 0, 0),
        ([0.1, 0, 0], 0, 0),
        ([0.25, 0, 0], 0.25, 0),
        ([0.25, 0.35, 0.05], 0.3, 0),
        ([0.25, 0.75, 0], 0.5, 0.75),
        ([6, 8, 0.05], 7, 7),
    ],
)
def test_mean_current_uses_load_specific_standby_threshold(currents, expected_consumer, expected_chargepoint):
    consumer = Consumer(1)
    chargepoint = Chargepoint(2, None)
    consumer.data.get.currents = currents
    chargepoint.data.get.currents = currents

    assert consumer.get_mean_current() == pytest.approx(expected_consumer)
    assert chargepoint.get_mean_current() == pytest.approx(expected_chargepoint)
