from modules.electricity_pricing.grid_fees.fixed_hours.config import FixedHoursGridFee
from modules.electricity_pricing.price_type import PriceType, get_price_type
from modules.electricity_pricing.flexible_tariffs.awattar.config import AwattarTariff
from modules.electricity_pricing.flexible_tariffs.energycharts.config import EnergyChartsTariff
from modules.electricity_pricing.timebased_tariffs.fixed_hours.config import FixedHoursTariff
from modules.electricity_pricing.fixed_tariffs.fixed_price.config import FixedPriceTariff
from modules.electricity_pricing.fixed_tariffs.fixed_price.tariff import create_electricity_tariff
from dataclasses import asdict

import pytest


@pytest.mark.parametrize("config, expected", [
    pytest.param(FixedPriceTariff(), PriceType.FIXED, id="fixed_price"),
    pytest.param(FixedHoursTariff(), PriceType.TIME_DEPENDENT, id="fixed_hours"),
    pytest.param(FixedHoursGridFee(), PriceType.TIME_DEPENDENT, id="grid_fee"),
    pytest.param(AwattarTariff(), PriceType.DYNAMIC, id="awattar"),
    pytest.param(EnergyChartsTariff(), PriceType.DYNAMIC, id="energycharts"),
])
def test_get_price_type(config, expected):
    assert get_price_type(config) == expected


def test_price_type_is_not_part_of_the_stored_configuration():
    assert "price_type" not in asdict(FixedPriceTariff())
    assert "price_type" not in asdict(FixedHoursTariff())


def test_fixed_price_tariff_provides_a_flat_price_list():
    config = FixedPriceTariff()
    config.configuration.default_price = 0.00027

    prices = create_electricity_tariff(config)().prices

    assert len(prices) == 144  # 36 Stunden in Viertelstunden
    assert set(prices.values()) == {0.00027}
