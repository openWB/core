from datetime import datetime, tzinfo
import time
from typing import Optional
from unittest.mock import Mock
from helpermodules import timecheck
import pytest

from modules.common.component_state import TariffState
from modules.common import configurable_tariff
from modules.common.configurable_tariff import ConfigurableFlexibleTariff, RETRY_BACKOFF_SECONDS
from modules.common.fault_state_level import FaultStateLevel
from modules.electricity_pricing.flexible_tariffs.awattar.config import AwattarTariff


def _patch_now(monkeypatch: pytest.MonkeyPatch, fixed_now: datetime) -> None:
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz: Optional[tzinfo] = None):
            return fixed_now if tz is None else fixed_now.replace(tzinfo=tz)

    monkeypatch.setattr(configurable_tariff, "datetime", FixedDateTime)
    monkeypatch.setattr(timecheck, "create_timestamp", Mock(return_value=fixed_now.timestamp()))


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

    latest_price_timestamp = datetime(2022, 5, 17, 13, 55, 0)

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

    latest_price_timestamp = datetime(2022, 5, 16, 12, 30, 0)

    # execution
    tariff._calculate_next_query_time(latest_price_timestamp)  # pyright: ignore[reportPrivateUsage]

    # evaluation
    expected_timestamp = int(latest_price_timestamp.timestamp())
    assert tariff.get.next_query_time == expected_timestamp


def test_no_new_prices_schedules_short_backoff_instead_of_stale_next_query_time(monkeypatch: pytest.MonkeyPatch):
    # Regression-Test für #3703: ohne neue Preise darf next_query_time nicht auf dem alten,
    # abgelaufenen Wert stehen bleiben - sonst wird jeden Regelzyklus neu abgefragt.
    fixed_now = datetime(2022, 5, 16, 13, 40, 0)
    _patch_now(monkeypatch, fixed_now)

    known_prices = {"1652700000": 10.72e-05}  # irgendein "heute"-Preis
    tariff = ConfigurableFlexibleTariff(
        AwattarTariff(), Mock(return_value=Mock(return_value=TariffState(prices=known_prices))))
    tariff.get.prices = known_prices
    tariff.get.next_query_time = int(fixed_now.timestamp()) - 10  # bereits abgelaufen, löst update() aus

    tariff.update()

    assert tariff.get.next_query_time == int(fixed_now.timestamp()) + RETRY_BACKOFF_SECONDS


def test_exception_schedules_short_backoff(monkeypatch: pytest.MonkeyPatch):
    # Regression-Test für #3703: next_query_time muss auch nach einer Exception weitergesetzt werden
    fixed_now = datetime(2022, 5, 16, 13, 40, 0)
    _patch_now(monkeypatch, fixed_now)

    tariff = ConfigurableFlexibleTariff(AwattarTariff(), Mock(return_value=Mock(side_effect=Exception("boom"))))
    tariff.get.next_query_time = int(fixed_now.timestamp()) - 10

    tariff.update()

    assert tariff.get.next_query_time == int(fixed_now.timestamp()) + RETRY_BACKOFF_SECONDS
    # fault_state wird unabhängig vom Fix schon von SingleComponentUpdateContext aus der Exception gesetzt
    assert tariff.fault_state.fault_state == FaultStateLevel.ERROR


def test_constructor_exception_is_logged_and_does_not_propagate(monkeypatch: pytest.MonkeyPatch):
    # Regression-Test: darf nicht reraisen, sonst bliebe bei subdata.py's Zuweisung das alte Modul aktiv
    tariff = ConfigurableFlexibleTariff(AwattarTariff(), Mock(side_effect=Exception("init failed")))

    assert tariff.fault_state.fault_state == FaultStateLevel.ERROR
    assert "init failed" in tariff.fault_state.fault_str
    assert not hasattr(tariff, "_component_updater")

    # update() bleibt für dieses dauerhaft fehlgeschlagene Modul ein sicherer No-op
    tariff.update()


def test_too_few_price_entries_error_is_not_overwritten_by_no_error(monkeypatch: pytest.MonkeyPatch):
    # Regression-Test für #3703: ein abschließendes no_error() darf den Fehler nicht überschreiben
    fixed_now = datetime(2022, 5, 16, 13, 40, 0)
    _patch_now(monkeypatch, fixed_now)

    known_prices = {"1652700000": 10.72e-05}  # nur ein Eintrag - zu wenig für eine Zeitschrittlänge
    tariff = ConfigurableFlexibleTariff(
        AwattarTariff(), Mock(return_value=Mock(return_value=TariffState(prices=known_prices))))
    tariff.get.next_query_time = int(fixed_now.timestamp()) - 10

    tariff.update()

    assert tariff.fault_state.fault_state == FaultStateLevel.ERROR


def test_no_tomorrow_prices_before_late_hour_is_not_a_warning(monkeypatch: pytest.MonkeyPatch):
    # Default tariff_update_hours=[14] + LATE_WARNING_OFFSET_HOURS=2 -> Warnschwelle 16:00.
    # 15:59 ist noch davor - "noch keine Preise für morgen" ist hier der normale, erwartete Fall.
    fixed_now = datetime(2022, 5, 16, 15, 59, 0)
    _patch_now(monkeypatch, fixed_now)

    now_ts = int(fixed_now.timestamp())
    known_prices = {str(now_ts + 3600): 10.72e-05, str(now_ts + 7200): 5.467e-05}  # +1h/+2h, noch nicht veraltet
    tariff = ConfigurableFlexibleTariff(
        AwattarTariff(), Mock(return_value=Mock(return_value=TariffState(prices=known_prices))))
    tariff.get.prices = known_prices
    tariff.get.next_query_time = int(fixed_now.timestamp()) - 10

    tariff.update()

    assert tariff.fault_state.fault_state == FaultStateLevel.NO_ERROR


def test_no_tomorrow_prices_after_late_hour_warns(monkeypatch: pytest.MonkeyPatch):
    # Warnschwelle 16:00 (siehe oben), 16:05 liegt knapp danach.
    fixed_now = datetime(2022, 5, 16, 16, 5, 0)
    _patch_now(monkeypatch, fixed_now)

    now_ts = int(fixed_now.timestamp())
    known_prices = {str(now_ts + 3600): 10.72e-05, str(now_ts + 7200): 5.467e-05}  # +1h/+2h, kein Eintrag für morgen
    tariff = ConfigurableFlexibleTariff(
        AwattarTariff(), Mock(return_value=Mock(return_value=TariffState(prices=known_prices))))
    tariff.get.prices = known_prices
    tariff.get.next_query_time = int(fixed_now.timestamp()) - 10

    tariff.update()

    assert tariff.fault_state.fault_state == FaultStateLevel.WARNING
    assert "Folgetag" in tariff.fault_state.fault_str


def test_dst_transition_does_not_shift_tomorrow_start(monkeypatch: pytest.MonkeyPatch):
    # Regression-Test: +24h in Sekunden trifft an Zeitumstellungstagen nicht auf Mitternacht (DE: 2026-10-25,
    # Umstellungstag hat 25 Stunden) - 23:30 wäre mit dem alten Bug fälschlich schon "morgen".
    monkeypatch.setenv("TZ", "Europe/Berlin")
    time.tzset()
    try:
        fixed_now = datetime(2026, 10, 25, 20, 0, 0)
        _patch_now(monkeypatch, fixed_now)

        now_ts = int(fixed_now.timestamp())
        known_prices = {str(now_ts + 3600): 10.72e-05, str(now_ts + 3*3600 + 1800): 5.467e-05}  # 21:00, 23:30
        tariff = ConfigurableFlexibleTariff(
            AwattarTariff(), Mock(return_value=Mock(return_value=TariffState(prices=known_prices))))
        tariff.get.prices = known_prices
        tariff.get.next_query_time = now_ts - 10

        tariff.update()

        assert tariff.fault_state.fault_state == FaultStateLevel.WARNING
    finally:
        time.tzset()


def test_tomorrow_prices_present_after_late_hour_does_not_warn(monkeypatch: pytest.MonkeyPatch):
    # Kein Fehlalarm, wenn die Preise für morgen bereits bekannt sind (z.B. aus einem früheren
    # erfolgreichen Abruf am selben Tag).
    fixed_now = datetime(2022, 5, 16, 16, 5, 0)
    _patch_now(monkeypatch, fixed_now)

    now_ts = int(fixed_now.timestamp())
    tomorrow_timestamp = str(int(datetime(2022, 5, 17, 0, 0, 0).timestamp()))
    known_prices = {str(now_ts - 3600): 10.72e-05, tomorrow_timestamp: 5.467e-05}
    tariff = ConfigurableFlexibleTariff(
        AwattarTariff(), Mock(return_value=Mock(return_value=TariffState(prices=known_prices))))
    tariff.get.prices = known_prices
    tariff.get.next_query_time = int(fixed_now.timestamp()) - 10

    tariff.update()

    assert tariff.fault_state.fault_state == FaultStateLevel.NO_ERROR
