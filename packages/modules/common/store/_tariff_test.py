from datetime import timedelta
import datetime
from typing import Dict
from unittest.mock import Mock

import pytest

from control import data
from control.optional import Optional
from modules.common.store._tariff import PriceValueStore


def make_prices(count, step, base):
    start = datetime.datetime.fromtimestamp(1761127200.0)  # 2025-10-22 12:00
    # json.loads macht keys immer zu str
    return {
        str((start + timedelta(minutes=step * i)).timestamp()): base + i
        for i in range(count)
    }


@pytest.fixture(autouse=True)
def mock_data() -> None:
    data.data_init(Mock())
    data.data.optional_data = Optional()


@pytest.mark.parametrize(
    "flexible_tariff, grid_fee, expected_prices",
    [
        pytest.param(
            make_prices(4, 15, 16),  # flexible_tariff: 4x15min
            make_prices(11, 5, 1),  # grid_fee: 11x5min
            {
                1761127200: 11,
                1761127500: 12,
                1761127800: 13,
                1761128100: 15,
                1761128400: 16,
                1761128700: 17,
                1761129000: 19,
                1761129300: 20,
                1761129600: 21,
                1761129900: 23,
                1761130200: 24,
            },
            id="grid_fee_finer",
        ),
        pytest.param(
            make_prices(12, 5, 13),  # flexible_tariff: 12x5min,
            make_prices(5, 14, 10),  # grid_fee: 5x14min
            {
                1761127200: 11,
                1761127500: 12,
                1761127800: 13,
                1761128100: 15,
                1761128400: 16,
                1761128700: 17,
                1761129000: 19,
                1761129300: 20,
                1761129600: 21,
                1761129900: 23,
                1761130200: 24,
                1761130500: 25,
            },
            id="flexible tariff finer",
        ),
        pytest.param(
            make_prices(5, 15, 13),  # flexible_tariff & grid_fee: 5x15min
            make_prices(5, 15, 10),
            {
                1761127200: 11,
                1761127500: 12,
                1761128100: 13,
                1761129000: 15,
                1761129900: 17,
                1761130800: 19,
            },
            id="same resolution",
        ),
    ],
)
def test_sum_prices(
    flexible_tariff: Dict[int, float],
    grid_fee: Dict[int, float],
    expected_prices: Dict[int, float],
):
    """
    It is expected that the flexible tariff contains a fix grid fee
    which is the median (the middle) of the distinct grid fee values.
    therefore the result is calculated like this:
        result = flexible_tariff_price + grid_fee_price - median_grid_fee
    """
    value_Store = PriceValueStore()
    data.data.optional_data.data.electricity_pricing.flexible_tariff.get.prices = (
        flexible_tariff
    )
    data.data.optional_data.data.electricity_pricing.grid_fee.get.prices = grid_fee
    summed = value_Store.sum_prices()
    for timestamp, price in summed.items():
        assert price == expected_prices[timestamp]
