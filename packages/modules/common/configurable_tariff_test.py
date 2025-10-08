
from unittest.mock import Mock
from helpermodules import timecheck
import pytest

from modules.common.component_state import TariffState
from modules.common.configurable_tariff import ConfigurableElectricityTariff
from modules.electricity_tariffs.awattar.config import AwattarTariff


@pytest.mark.parametrize(
    "now, tariff_state, expected",
    [
        pytest.param(1652680800,
                     TariffState(prices={"1652680800": -5.87e-06,
                                         "1652684400": 5.467e-05,
                                         "1652688000": 10.72e-05}),
                     TariffState(prices={"1652680800": -5.87e-06,
                                         "1652684400": 5.467e-05,
                                         "1652688000": 10.72e-05}), id="keine veralteten Einträge"),
        pytest.param(1652680800,
                     TariffState(prices={"1652677200": -5.87e-06,
                                         "1652680800": 5.467e-05,
                                         "1652684400": 10.72e-05}),
                     TariffState(prices={"1652680800": 5.467e-05,
                                         "1652684400": 10.72e-05}), id="Lösche ersten Eintrag"),
        pytest.param(1652684000,
                     TariffState(prices={"1652680800": -5.87e-06,
                                         "1652684400": 5.467e-05,
                                         "1652688000": 10.72e-05}),
                     TariffState(prices={"1652680800": -5.87e-06,
                                         "1652684400": 5.467e-05,
                                         "1652688000": 10.72e-05}), id="erster time slot noch nicht zu Ende"),
        pytest.param(1652684000,
                     TariffState(prices={"1652680000": -5.87e-06,
                                         "1652681200": 5.467e-05,
                                         "1652682400": 10.72e-05,
                                         "1652683600": 10.72e-05,
                                         "1652684800": 10.72e-05,
                                         "1652686000": 10.72e-05,
                                         "1652687200": 10.72e-05}),
                     TariffState(prices={"1652683600": 10.72e-05,
                                         "1652684800": 10.72e-05,
                                         "1652686000": 10.72e-05,
                                         "1652687200": 10.72e-05}), id="20 Minuten time slots"),
    ],
)
def test_remove_outdated_prices(now: int, tariff_state: TariffState, expected: TariffState, monkeypatch):
    # setup
    tariff = ConfigurableElectricityTariff(AwattarTariff(), Mock())
    time_slot_seconds = [int(timestamp) for timestamp in tariff_state.prices.keys()][:2]

    # Montag 16.05.2022, 8:40:52  "05/16/2022, 08:40:52" Unix: 1652683252
    monkeypatch.setattr(timecheck,
                        "create_timestamp",
                        Mock(return_value=now))

    # test
    result = tariff._remove_outdated_prices(tariff_state, time_slot_seconds[1]-time_slot_seconds[0])

    # assert
    assert result.prices == expected.prices


def test_accept_no_prices_at_start(monkeypatch):
    # setup
    tariff = ConfigurableElectricityTariff(
        AwattarTariff(),
        Mock(return_value=TariffState(
            prices={"5": 10.72e-05,
                    "6": 10.72e-05,
                    "7": 10.72e-05,
                    "8": 10.72e-05})))

    # Montag 16.05.2022, 8:40:52  "05/16/2022, 08:40:52" Unix: 1652683252
    monkeypatch.setattr(timecheck,
                        "create_timestamp",
                        Mock(return_value=5))

    # test - do not fail
    tariff._remove_outdated_prices(TariffState(), 1)
