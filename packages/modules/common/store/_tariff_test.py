from datetime import timedelta
import datetime
from typing import Dict
from unittest.mock import Mock

import pytest

from control import data
from control.optional import Optional
from modules.common.store._tariff import PriceValueStore


def make_prices(count, step, base):
    start = datetime.datetime(2025, 10, 22, 12, 0)
    # json.loads macht keys immer zu str
    return {str((start + timedelta(minutes=step*i)).timestamp()): base+i for i in range(count)}


@pytest.fixture(autouse=True)
def mock_data() -> None:
    data.data_init(Mock())
    data.data.optional_data = Optional()


@pytest.mark.parametrize("flexible_tariff, grid_fee, expected_prices", [
    pytest.param(make_prices(4, 15, 10), make_prices(12, 5, 1), {1761127200: 11,
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
                                                                 1761130500: 25},
                 id="grid_fee_finer"),  # grid_fee: 12x5min, flexible_tariff: 4x15min
    pytest.param(make_prices(12, 5, 1), make_prices(4, 14, 10), {1761127200: 11,
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
                                                                 1761130500: 25},
                 id="flexible tariff finer"),  # flexible_tariff: 12x5min, grid_fee: 4x14min
    pytest.param(make_prices(4, 15, 1), make_prices(4, 15, 10), {1761127200: 11,
                                                                 1761128100: 13,
                                                                 1761129000: 15,
                                                                 1761129900: 17},
                 id="same resolution"),  # flexible_tariff & grid_fee: 4x15min
])
def test_sum_prices(flexible_tariff: Dict[int, float],
                    grid_fee: Dict[int, float],
                    expected_prices: Dict[int, float]):
    value_Store = PriceValueStore()
    data.data.optional_data.data.electricity_pricing.flexible_tariff.get.prices = flexible_tariff
    data.data.optional_data.data.electricity_pricing.grid_fee.get.prices = grid_fee
    summed = value_Store.sum_prices()
    for timestamp, price in summed.items():
        assert price == expected_prices[timestamp]
