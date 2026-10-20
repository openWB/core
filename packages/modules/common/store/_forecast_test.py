import time
from datetime import datetime
from typing import Optional as TypingOptional
from unittest.mock import Mock

import pytest

from control import data
from control.optional import Optional
from modules.common.component_state import ForecastState
from modules.common.store import _forecast
from modules.common.store._forecast import ForecastValueStore


@pytest.fixture(autouse=True)
def mock_data() -> None:
    data.data_init(Mock())
    data.data.optional_data = Optional()


def _patch_now(monkeypatch: pytest.MonkeyPatch, fixed_now: datetime) -> None:
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz: TypingOptional[object] = None):
            return fixed_now

    monkeypatch.setattr(_forecast, "datetime", FixedDateTime)


def _get() -> _forecast.ForecastValueStore:
    return data.data.optional_data.data.forecast.get


def test_update_splits_by_current_calendar_day(monkeypatch: pytest.MonkeyPatch):
    _patch_now(monkeypatch, datetime(2026, 10, 20, 8, 0, 0))
    values = {
        str(int(datetime(2026, 10, 20, 10, 0, 0).timestamp())): 500.0,
        str(int(datetime(2026, 10, 21, 10, 0, 0).timestamp())): 700.0,
    }
    store = ForecastValueStore()
    store.set(ForecastState(forecast_values=values, daily_kwh={"2026-10-20": 3.5, "2026-10-21": 4.2}))

    store.update()

    assert data.data.optional_data.data.forecast.get.today_kwh == 3.5
    assert data.data.optional_data.data.forecast.get.tomorrow_kwh == 4.2
    assert list(data.data.optional_data.data.forecast.get.today_values.values()) == [500.0]
    assert list(data.data.optional_data.data.forecast.get.tomorrow_values.values()) == [700.0]


def test_update_reruns_split_after_midnight_without_new_fetch(monkeypatch: pytest.MonkeyPatch):
    # Regression-Test: derselbe (unveränderte) Datensatz muss nach Mitternacht korrekt neu
    # zugeordnet werden, auch ohne dass zwischenzeitlich ein neuer Abruf stattgefunden hat.
    values = {
        str(int(datetime(2026, 10, 20, 10, 0, 0).timestamp())): 500.0,
        str(int(datetime(2026, 10, 21, 10, 0, 0).timestamp())): 700.0,
    }
    daily_kwh = {"2026-10-20": 3.5, "2026-10-21": 4.2}
    store = ForecastValueStore()
    store.set(ForecastState(forecast_values=values, daily_kwh=daily_kwh))

    _patch_now(monkeypatch, datetime(2026, 10, 20, 23, 50, 0))
    store.update()
    assert data.data.optional_data.data.forecast.get.today_kwh == 3.5
    assert data.data.optional_data.data.forecast.get.tomorrow_kwh == 4.2

    _patch_now(monkeypatch, datetime(2026, 10, 21, 0, 5, 0))
    store.update()
    assert data.data.optional_data.data.forecast.get.today_kwh == 4.2
    assert data.data.optional_data.data.forecast.get.tomorrow_kwh == 0.0


def test_update_safe_before_first_fetch():
    # ForecastValueStore() muss schon vor dem ersten set() aufrufbar sein (siehe
    # ConfigurableForecast.update(), das update() auch ohne fälligen Abruf jeden Zyklus ruft)
    ForecastValueStore().update()


def test_dst_transition_does_not_shift_day_boundary(monkeypatch: pytest.MonkeyPatch):
    # Regression-Test: an Zeitumstellungstagen hat der lokale Tag 23 oder 25 Stunden - die
    # Kalendertag-Zuordnung darf trotzdem nicht verrutschen.
    monkeypatch.setenv("TZ", "Europe/Berlin")
    time.tzset()
    try:
        values = {
            str(int(datetime(2026, 10, 25, 23, 30, 0).timestamp())): 100.0,
            str(int(datetime(2026, 10, 26, 0, 30, 0).timestamp())): 200.0,
        }
        store = ForecastValueStore()
        store.set(ForecastState(forecast_values=values, daily_kwh={}))

        _patch_now(monkeypatch, datetime(2026, 10, 25, 20, 0, 0))
        store.update()

        assert list(data.data.optional_data.data.forecast.get.today_values.values()) == [100.0]
        assert list(data.data.optional_data.data.forecast.get.tomorrow_values.values()) == [200.0]
    finally:
        time.tzset()
