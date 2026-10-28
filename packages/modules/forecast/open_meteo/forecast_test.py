from datetime import datetime, timedelta
from unittest.mock import Mock

from modules.common import req
from modules.forecast.open_meteo import forecast
from modules.forecast.open_meteo.config import OpenMeteoForecastConfiguration


def test_horizon_covers_full_day_after_tomorrow_from_last_daily_fetch():
    # bei Abruf um 20 Uhr muss "übermorgen" (= "morgen" direkt nach Mitternacht, vor dem ersten
    # Abruf des neuen Tages um 5 Uhr) noch vollständig enthalten sein
    assert forecast.OPEN_METEO_FORECAST_HOURS >= 52


def test_fetch_forecast_respects_horizon(monkeypatch):
    start = datetime(2026, 10, 20, 0, 0, 0)
    hours = forecast.OPEN_METEO_FORECAST_HOURS + 12
    times = [(start + timedelta(hours=i)).isoformat() for i in range(hours)]
    radiation = [100.0] * hours
    response = Mock()
    response.json.return_value = {"hourly": {"time": times, "global_tilted_irradiance": radiation}}
    session = Mock()
    session.get.return_value = response
    monkeypatch.setattr(req, "get_http_session", Mock(return_value=session))

    config = OpenMeteoForecastConfiguration(
        latitude=50.0, longitude=10.0, timezone="Europe/Berlin",
        strings=[{"name": None, "peak_power_kw": 5.0, "tilt": 30.0, "azimuth": 180.0}],
    )

    values, _ = forecast.fetch_forecast(config)

    assert len(values) == forecast.OPEN_METEO_FORECAST_HOURS
