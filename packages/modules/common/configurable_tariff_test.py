from datetime import datetime, tzinfo
from typing import Optional
from unittest.mock import Mock
from helpermodules import timecheck
import pytest

from modules.common.component_state import TariffState
from modules.common import configurable_tariff
from modules.common.configurable_tariff import ConfigurableFlexibleTariff
from modules.electricity_pricing.flexible_tariffs.awattar.config import AwattarTariff


@pytest.mark.parametrize(
    "now, tariff_state, expected",
    [
        pytest.param(
            1652680800,
            TariffState(
                prices={
                    "1652680800": -5.87e-06,
                    "1652684400": 5.467e-05,
                    "1652688000": 10.72e-05,
                }
            ),
            TariffState(
                prices={
                    "1652680800": -5.87e-06,
                    "1652684400": 5.467e-05,
                    "1652688000": 10.72e-05,
                }
            ),
            id="keine veralteten Einträge",
        ),
        pytest.param(
            1652680800,
            TariffState(
                prices={
                    "1652677200": -5.87e-06,
                    "1652680800": 5.467e-05,
                    "1652684400": 10.72e-05,
                }
            ),
            TariffState(prices={"1652680800": 5.467e-05, "1652684400": 10.72e-05}),
            id="Lösche ersten Eintrag",
        ),
        pytest.param(
            1652684000,
            TariffState(
                prices={
                    "1652680800": -5.87e-06,
                    "1652684400": 5.467e-05,
                    "1652688000": 10.72e-05,
                }
            ),
            TariffState(
                prices={
                    "1652680800": -5.87e-06,
                    "1652684400": 5.467e-05,
                    "1652688000": 10.72e-05,
                }
            ),
            id="erster time slot noch nicht zu Ende",
        ),
        pytest.param(
            1652684000,
            TariffState(
                prices={
                    "1652680000": -5.87e-06,
                    "1652681200": 5.467e-05,
                    "1652682400": 10.72e-05,
                    "1652683600": 10.72e-05,
                    "1652684800": 10.72e-05,
                    "1652686000": 10.72e-05,
                    "1652687200": 10.72e-05,
                }
            ),
            TariffState(
                prices={
                    "1652683600": 10.72e-05,
                    "1652684800": 10.72e-05,
                    "1652686000": 10.72e-05,
                    "1652687200": 10.72e-05,
                }
            ),
            id="20 Minuten time slots",
        ),
    ],
)
def test_remove_outdated_prices(
    now: int, tariff_state: TariffState, expected: TariffState, monkeypatch
):
    # setup
    tariff = ConfigurableFlexibleTariff(AwattarTariff(), Mock())
    time_slot_seconds = [int(timestamp) for timestamp in tariff_state.prices.keys()][:2]

    # Montag 16.05.2022, 8:40:52  "05/16/2022, 08:40:52" Unix: 1652683252
    monkeypatch.setattr(timecheck, "create_timestamp", Mock(return_value=now))

    # test
    # pyright: ignore[reportPrivateUsage]
    result = tariff._remove_outdated_prices(tariff_state, time_slot_seconds[1] - time_slot_seconds[0])

    # assert
    assert result.prices == expected.prices


def test_accept_no_prices_at_start(monkeypatch):
    # setup
    tariff = ConfigurableFlexibleTariff(
        AwattarTariff(),
        Mock(
            return_value=TariffState(
                prices={"5": 10.72e-05, "6": 10.72e-05, "7": 10.72e-05, "8": 10.72e-05}
            )
        ),
    )

    # Montag 16.05.2022, 8:40:52  "05/16/2022, 08:40:52" Unix: 1652683252
    monkeypatch.setattr(timecheck, "create_timestamp", Mock(return_value=5))

    # test - do not fail
    tariff._remove_outdated_prices(TariffState(), 1)  # pyright: ignore[reportPrivateUsage]


def test_calculate_next_query_time(monkeypatch: pytest.MonkeyPatch):
    # setup
    fixed_now = datetime(2022, 5, 16, 10, 10, 0)

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz: Optional[tzinfo] = None):
            return fixed_now if tz is None else fixed_now.replace(tzinfo=tz)

    monkeypatch.setattr(configurable_tariff, "datetime", FixedDateTime)
    monkeypatch.setattr(configurable_tariff.random, "randint", Mock(return_value=1))

    tariff = ConfigurableFlexibleTariff(AwattarTariff(), Mock(return_value=Mock()))
    tariff.tariff_update_hours = [14]

    latest_price_timestamp = datetime(2022, 5, 16, 13, 55, 0)

    # execution
    tariff._calculate_next_query_time(latest_price_timestamp)  # pyright: ignore[reportPrivateUsage]

    # evaluation
    expected_timestamp = int(datetime(2022, 5, 16, 13, 55, 0).timestamp())
    assert tariff.get.next_query_time == expected_timestamp


def test_calculate_next_query_time_uses_latest_price_timestamp(monkeypatch: pytest.MonkeyPatch):
    # setup
    fixed_now = datetime(2022, 5, 16, 10, 10, 0)

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz: Optional[tzinfo] = None):
            return fixed_now if tz is None else fixed_now.replace(tzinfo=tz)

    monkeypatch.setattr(configurable_tariff, "datetime", FixedDateTime)
    monkeypatch.setattr(configurable_tariff.random, "randint", Mock(return_value=1))

    tariff = ConfigurableFlexibleTariff(AwattarTariff(), Mock(return_value=Mock()))
    tariff.tariff_update_hours = [14]

    latest_price_timestamp = datetime(2022, 5, 16, 14, 30, 0)

    # execution
    tariff._calculate_next_query_time(latest_price_timestamp)  # pyright: ignore[reportPrivateUsage]

    # evaluation
    expected_timestamp = int(latest_price_timestamp.timestamp())
    assert tariff.get.next_query_time == expected_timestamp
