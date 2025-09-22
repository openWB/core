
from unittest.mock import Mock
import pytest

from modules.common.component_state import TariffState
from modules.common.configurable_tariff import ConfigurableElectricityTariff
from modules.electricity_tariffs.awattar.config import AwattarTariff


@pytest.mark.parametrize(
    "tariff_state, expected",
    [
        pytest.param(TariffState(prices={"1652680800": -5.87e-06,
                                         "1652684400": 5.467e-05,
                                         "1652688000": 10.72e-05}),
                     TariffState(prices={"1652680800": -5.87e-06,
                                         "1652684400": 5.467e-05,
                                         "1652688000": 10.72e-05}), id="keine veralteten Einträge"),
        pytest.param(TariffState(prices={"1652677200": -5.87e-06,
                                         "1652680800": 5.467e-05,
                                         "1652684400": 10.72e-05}),
                     TariffState(prices={"1652680800": 5.467e-05,
                                         "1652684400": 10.72e-05}), id="Lösche ersten Eintrag"),
    ],
)
def test_remove_outdated_prices(tariff_state: TariffState, expected: TariffState, monkeypatch):
    # setup
    tariff = ConfigurableElectricityTariff(AwattarTariff(), Mock())

    # test
    result = tariff._remove_outdated_prices(tariff_state)

    # assert
    assert result.prices == expected.prices
