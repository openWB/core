from datetime import datetime, tzinfo
import time
from typing import Optional
from unittest.mock import Mock
from helpermodules import timecheck
import pytest
import requests

from modules.common.component_state import TariffState
from modules.common import configurable_tariff
from modules.common.configurable_tariff import (ConfigurableFlexibleTariff, PERMANENT_ERROR_PARK_SECONDS,
                                                RETRY_BACKOFF_SECONDS, RETRY_INTERVAL_SECONDS)
from modules.common.tariff_errors import PermanentTariffError
from modules.common.fault_state_level import FaultStateLevel
from modules.electricity_pricing.flexible_tariffs.awattar.config import AwattarTariff
from modules.electricity_pricing.flexible_tariffs.ekz.config import EkzTariff
from modules.electricity_pricing.flexible_tariffs.rabot.config import RabotTariff
from modules.electricity_pricing.flexible_tariffs.smart_energy.config import SmartEnergyTariff
from modules.electricity_pricing.flexible_tariffs.westfalen_wind.config import WestfalenWindTariff


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


def _prices_until(end: datetime, step_minutes: int = 15) -> dict:
    # Viertelstunden-Preise von 2022-05-16 00:00 bis end (inklusive)
    prices = {}
    slot = datetime(2022, 5, 16, 0, 0, 0)
    while slot <= end:
        prices[str(int(slot.timestamp()))] = 1e-4
        slot = datetime.fromtimestamp(slot.timestamp() + step_minutes * 60)
    return prices


def _last_slot_of_the_previous_day() -> dict:
    return {str(int(datetime(2022, 5, 15, 23, 45, 0).timestamp())): 1e-4}


def _schedule(monkeypatch: pytest.MonkeyPatch, now: datetime, prices: dict, config=None) -> int:
    _patch_now(monkeypatch, now)
    monkeypatch.setattr(configurable_tariff.random, "randint", Mock(return_value=6))  # 30 Minuten vor 14 Uhr
    tariff = ConfigurableFlexibleTariff(config or AwattarTariff(), Mock(return_value=Mock()))
    tariff._schedule_next_query(prices, 900)  # pyright: ignore[reportPrivateUsage]
    return tariff.get.next_query_time


def test_next_query_is_the_first_try_of_tomorrow_when_tomorrow_is_known(monkeypatch: pytest.MonkeyPatch):
    next_query = _schedule(monkeypatch, datetime(2022, 5, 16, 14, 10, 0), _prices_until(datetime(2022, 5, 17, 23, 45)))

    assert next_query == int(datetime(2022, 5, 17, 13, 30, 0).timestamp())


def test_first_try_is_5_to_30_minutes_before_14(monkeypatch: pytest.MonkeyPatch):
    _patch_now(monkeypatch, datetime(2022, 5, 16, 10, 10, 0))
    randint = Mock(return_value=1)
    monkeypatch.setattr(configurable_tariff.random, "randint", randint)
    tariff = ConfigurableFlexibleTariff(AwattarTariff(), Mock(return_value=Mock()))

    prices = _prices_until(datetime(2022, 5, 17, 23, 45))

    tariff._schedule_next_query(prices, 900)  # pyright: ignore[reportPrivateUsage]

    randint.assert_called_once_with(1, 6)
    assert tariff.get.next_query_time == int(datetime(2022, 5, 17, 13, 55, 0).timestamp())


def test_tomorrow_missing_before_the_first_try_waits_for_the_first_try(monkeypatch: pytest.MonkeyPatch):
    # morgens, oder nach Mitternacht: die Wiederholung vom Vortag endet, der nächste Abruf ist der erste des Tages
    next_query = _schedule(monkeypatch, datetime(2022, 5, 16, 0, 10, 0), _prices_until(datetime(2022, 5, 16, 23, 45)))

    assert next_query == int(datetime(2022, 5, 16, 13, 30, 0).timestamp())


def test_tomorrow_missing_after_the_first_try_retries_hourly(monkeypatch: pytest.MonkeyPatch):
    now = datetime(2022, 5, 16, 14, 10, 0)

    next_query = _schedule(monkeypatch, now, _prices_until(datetime(2022, 5, 16, 23, 45)))

    assert next_query == int(now.timestamp()) + RETRY_INTERVAL_SECONDS


def test_no_price_for_the_current_time_retries_hourly(monkeypatch: pytest.MonkeyPatch):
    now = datetime(2022, 5, 16, 0, 10, 0)

    next_query = _schedule(monkeypatch, now, _last_slot_of_the_previous_day())

    assert next_query == int(now.timestamp()) + RETRY_INTERVAL_SECONDS


def test_provider_with_prices_of_the_current_day_retries_quickly_after_midnight(monkeypatch: pytest.MonkeyPatch):
    now = datetime(2022, 5, 16, 0, 3, 0)

    next_query = _schedule(monkeypatch, now, _last_slot_of_the_previous_day(), config=WestfalenWindTariff())

    assert next_query == int(now.timestamp()) + RETRY_BACKOFF_SECONDS


def test_provider_with_prices_of_the_current_day_is_queried_when_the_prices_end(monkeypatch: pytest.MonkeyPatch):
    # z.B. Westfalen Wind: Preise des Tages ab 0 Uhr, kein Folgetag
    next_query = _schedule(monkeypatch, datetime(2022, 5, 16, 14, 10, 0), _prices_until(datetime(2022, 5, 16, 23, 45)),
                           config=WestfalenWindTariff())

    assert next_query == int(datetime(2022, 5, 17, 0, 0, 0).timestamp())


def test_next_query_is_not_later_than_the_end_of_the_known_prices(monkeypatch: pytest.MonkeyPatch):
    # die Preise enden morgen um 13:00, noch vor dem ersten Abruf des Tages (13:30)
    next_query = _schedule(monkeypatch, datetime(2022, 5, 16, 0, 30, 0), _prices_until(datetime(2022, 5, 17, 12, 45)))

    assert next_query == int(datetime(2022, 5, 17, 13, 0, 0).timestamp())


@pytest.mark.parametrize("config", [AwattarTariff(), EkzTariff(), RabotTariff(), SmartEnergyTariff()],
                         ids=lambda config: config.type)
def test_all_day_ahead_providers_share_the_same_schedule(monkeypatch: pytest.MonkeyPatch, config):
    next_query = _schedule(monkeypatch, datetime(2022, 5, 16, 10, 10, 0), _prices_until(datetime(2022, 5, 16, 23, 45)),
                           config=config)

    assert next_query == int(datetime(2022, 5, 16, 13, 30, 0).timestamp())


@pytest.mark.parametrize("now, expected", [
    pytest.param(datetime(2022, 5, 16, 18, 59, 0), FaultStateLevel.NO_ERROR, id="vor 19 Uhr"),
    pytest.param(datetime(2022, 5, 16, 19, 5, 0), FaultStateLevel.WARNING, id="nach 19 Uhr")])
def test_missing_tomorrow_warns_from_19_for_every_provider(monkeypatch: pytest.MonkeyPatch, now, expected):
    _patch_now(monkeypatch, now)
    now_ts = int(now.timestamp())
    known_prices = {str(now_ts + 300): 10.72e-05, str(now_ts + 1200): 5.467e-05}
    tariff = ConfigurableFlexibleTariff(
        EkzTariff(), Mock(return_value=Mock(return_value=TariffState(prices=known_prices))))
    tariff.get.prices = known_prices
    tariff.get.next_query_time = now_ts - 10

    tariff.update()

    assert tariff.fault_state.fault_state == expected


def test_empty_response_is_retried_hourly(monkeypatch: pytest.MonkeyPatch):
    now = datetime(2022, 5, 16, 14, 10, 0)

    next_query = _schedule(monkeypatch, now, {})

    assert next_query == int(now.timestamp()) + RETRY_INTERVAL_SECONDS


def test_schedule_is_published_after_the_prices_are_stored(monkeypatch: pytest.MonkeyPatch):
    # bricht das Speichern ab, darf der Zeitplan der neuen Antwort nicht schon gelten
    fixed_now = datetime(2022, 5, 16, 14, 10, 0)
    _patch_now(monkeypatch, fixed_now)
    newer = _prices_until(datetime(2022, 5, 17, 23, 45))
    tariff = ConfigurableFlexibleTariff(
        AwattarTariff(), Mock(return_value=Mock(return_value=TariffState(prices=newer))))
    tariff.get.prices = {}
    tariff.get.next_query_time = int(fixed_now.timestamp()) - 10
    tariff.store.set = Mock()
    tariff.store.update = Mock(side_effect=Exception("Speichern fehlgeschlagen"))

    tariff.update()

    assert tariff.get.next_query_time == int(fixed_now.timestamp()) + RETRY_BACKOFF_SECONDS


def test_prices_stored_by_another_update_while_fetching_are_not_overwritten(monkeypatch: pytest.MonkeyPatch):
    _patch_now(monkeypatch, datetime(2022, 5, 16, 14, 10, 0))
    newer = _prices_until(datetime(2022, 5, 17, 23, 45))
    older = _prices_until(datetime(2022, 5, 16, 23, 45))

    def slow_fetch() -> TariffState:
        tariff.get.prices = newer  # ein anderer Abruf hat währenddessen neuere Preise gespeichert
        return TariffState(prices=older)

    tariff = ConfigurableFlexibleTariff(AwattarTariff(), Mock(return_value=slow_fetch))
    tariff.get.prices = {}

    state = tariff._ConfigurableTariff__call_component_updater()  # pyright: ignore[reportPrivateUsage]

    assert state.prices == newer


def test_known_prices_are_kept_when_the_provider_returns_nothing_newer(monkeypatch: pytest.MonkeyPatch):
    _patch_now(monkeypatch, datetime(2022, 5, 16, 14, 10, 0))
    known = _prices_until(datetime(2022, 5, 17, 23, 45))
    older = _prices_until(datetime(2022, 5, 16, 23, 45))
    tariff = ConfigurableFlexibleTariff(
        AwattarTariff(), Mock(return_value=Mock(return_value=TariffState(prices=older))))
    tariff.get.prices = known

    state = tariff._ConfigurableTariff__call_component_updater()  # pyright: ignore[reportPrivateUsage]

    assert state.prices == known


def test_newer_prices_replace_the_known_prices(monkeypatch: pytest.MonkeyPatch):
    _patch_now(monkeypatch, datetime(2022, 5, 16, 14, 10, 0))
    newer = _prices_until(datetime(2022, 5, 17, 23, 45))
    tariff = ConfigurableFlexibleTariff(
        AwattarTariff(), Mock(return_value=Mock(return_value=TariffState(prices=newer))))
    tariff.get.prices = _prices_until(datetime(2022, 5, 16, 23, 45))

    state = tariff._ConfigurableTariff__call_component_updater()  # pyright: ignore[reportPrivateUsage]

    assert state.prices == newer


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

    assert tariff.get.next_query_time == int(fixed_now.timestamp()) + RETRY_INTERVAL_SECONDS


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
    # Warnschwelle ist 19:00 (TOMORROW_WARNING_HOUR).
    # 18:59 ist noch davor - "noch keine Preise für morgen" ist hier der normale, erwartete Fall.
    fixed_now = datetime(2022, 5, 16, 18, 59, 0)
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
    # Warnschwelle 19:00 (siehe oben), 19:05 liegt knapp danach.
    fixed_now = datetime(2022, 5, 16, 19, 5, 0)
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
    fixed_now = datetime(2022, 5, 16, 19, 5, 0)
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


def test_provider_with_prices_of_the_current_day_does_not_warn_about_tomorrow(monkeypatch: pytest.MonkeyPatch):
    fixed_now = datetime(2022, 5, 16, 19, 5, 0)
    _patch_now(monkeypatch, fixed_now)

    now_ts = int(fixed_now.timestamp())
    known_prices = {str(now_ts + 3600): 10.72e-05, str(now_ts + 7200): 5.467e-05}
    tariff = ConfigurableFlexibleTariff(
        WestfalenWindTariff(), Mock(return_value=Mock(return_value=TariffState(prices=known_prices))))
    tariff.get.prices = known_prices
    tariff.get.next_query_time = now_ts - 10

    tariff.update()

    assert tariff.fault_state.fault_state == FaultStateLevel.NO_ERROR


def _http_error(status_code: int) -> requests.HTTPError:
    return requests.HTTPError(response=Mock(status_code=status_code))


@pytest.mark.parametrize("exception", [PermanentTariffError("Anmeldung fehlgeschlagen"), _http_error(401),
                                       _http_error(403)])
def test_permanent_error_stops_the_queries_until_the_configuration_changes(monkeypatch: pytest.MonkeyPatch, exception):
    fixed_now = datetime(2022, 5, 16, 13, 40, 0)
    _patch_now(monkeypatch, fixed_now)

    tariff = ConfigurableFlexibleTariff(AwattarTariff(), Mock(return_value=Mock(side_effect=exception)))
    tariff.get.next_query_time = int(fixed_now.timestamp()) - 10

    tariff.update()

    assert tariff.get.next_query_time == int(fixed_now.timestamp()) + PERMANENT_ERROR_PARK_SECONDS
    assert tariff.fault_state.fault_state == FaultStateLevel.ERROR
    assert "Konfiguration" in tariff.fault_state.fault_str


@pytest.mark.parametrize("exception", [_http_error(500), _http_error(404), Exception("boom")])
def test_other_errors_are_retried_soon(monkeypatch: pytest.MonkeyPatch, exception):
    fixed_now = datetime(2022, 5, 16, 13, 40, 0)
    _patch_now(monkeypatch, fixed_now)

    tariff = ConfigurableFlexibleTariff(AwattarTariff(), Mock(return_value=Mock(side_effect=exception)))
    tariff.get.next_query_time = int(fixed_now.timestamp()) - 10

    tariff.update()

    assert tariff.get.next_query_time == int(fixed_now.timestamp()) + RETRY_BACKOFF_SECONDS
