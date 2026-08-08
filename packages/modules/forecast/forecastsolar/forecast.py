from datetime import datetime
import logging
from typing import Any, Dict, Tuple
from requests import HTTPError

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ForecastState

from modules.forecast.forecastsolar.config import ForecastSolar, ForecastSolarConfiguration


log = logging.getLogger("forecast")


def _require(value, field_name: str):
    if value is None:
        raise ValueError(f"Missing required forecast config field: {field_name}")
    if isinstance(value, str) and value.strip() == "":
        raise ValueError(f"Missing required forecast config field: {field_name}")
    return value


def _log_forecast_solar_rate_limit(payload: dict, headers: dict, url: str) -> None:
    message = payload.get("message") if isinstance(payload, dict) else None
    ratelimit = message.get("ratelimit") if isinstance(message, dict) else None
    if not isinstance(ratelimit, dict):
        return
    retry_at = ratelimit.get("retry-at") or headers.get("X-Ratelimit-Retry-At")
    remaining = ratelimit.get("remaining") or headers.get("X-Ratelimit-Remaining")
    limit = ratelimit.get("limit") or headers.get("X-Ratelimit-Limit")
    period = ratelimit.get("period") or headers.get("X-Ratelimit-Period")
    log.info(
        "Forecast.Solar ratelimit info for %s: remaining=%s limit=%s period=%s retry_at=%s",
        url,
        remaining,
        limit,
        period,
        retry_at,
    )


def _parse_forecast_solar_response(payload: Dict) -> Tuple[Dict[str, float], Dict[str, float]]:
    result = payload.get("result") if isinstance(payload, dict) else None
    source = result if isinstance(result, dict) else payload

    watts = source.get("watts") if isinstance(source, dict) else None
    if watts is None and isinstance(source, dict):
        watts = source.get("values")
    if watts is None and isinstance(source, dict):
        watts = source.get("data")

    values: Dict[str, float] = {}
    if isinstance(watts, dict):
        for timestamp, value in watts.items():
            if value is None:
                continue
            timestamp_key = str(int(datetime.fromisoformat(timestamp).timestamp()))
            values[timestamp_key] = float(value)

    daily_source = source.get("watt_hours_day") if isinstance(source, dict) else None
    daily_kwh: Dict[str, float] = {}
    if isinstance(daily_source, dict):
        for date_key, value in daily_source.items():
            if value is None:
                continue
            daily_kwh[str(date_key)] = float(value) / 1000.0

    return values, daily_kwh


def fetch_forecast(config: ForecastSolarConfiguration) -> Tuple[Dict[str, float], Dict[str, float]]:
    latitude = _require(config.latitude, "latitude")
    longitude = _require(config.longitude, "longitude")
    string_configs_raw = _require(config.strings, "strings")
    if not isinstance(string_configs_raw, list) or len(string_configs_raw) == 0:
        raise ValueError("Missing required forecast config field: strings")
    string_configs: list[dict[str, Any]] = string_configs_raw
    if len(string_configs) > 6:
        string_configs = string_configs[:6]

    values: Dict[str, float] = {}
    daily_kwh: Dict[str, float] = {}

    for string_config in string_configs:
        peak_power_kw = float(_require(string_config.get("peak_power_kw"), "strings[].peak_power_kw"))
        if peak_power_kw <= 0:
            raise ValueError("Missing required forecast config field: strings[].peak_power_kw")
        azimuth = _require(string_config.get("azimuth"), "strings[].azimuth")
        tilt = _require(string_config.get("tilt"), "strings[].tilt")

        url = (
            "https://api.forecast.solar/estimate/watthours"
            f"/{latitude}"
            f"/{longitude}"
            f"/{tilt}"
            f"/{azimuth}"
            f"/{peak_power_kw}"
        )
        try:
            response_obj = req.get_http_session().get(url, timeout=(2, 6))
        except HTTPError as e:
            response = e.response
            if response is not None and response.status_code == 429:
                retry_at = response.headers.get("X-Ratelimit-Retry-At")
                remaining = response.headers.get("X-Ratelimit-Remaining")
                limit = response.headers.get("X-Ratelimit-Limit")
                period = response.headers.get("X-Ratelimit-Period")
                log.warning(
                    "Forecast.Solar rate limit hit for %s: remaining=%s limit=%s period=%s retry_at=%s",
                    url,
                    remaining,
                    limit,
                    period,
                    retry_at,
                )
            raise

        response = response_obj.json()
        _log_forecast_solar_rate_limit(response, dict(response_obj.headers), url)
        string_values, string_daily_kwh = _parse_forecast_solar_response(response)
        for timestamp, value in string_values.items():
            values[timestamp] = values.get(timestamp, 0.0) + value
        for day, value in string_daily_kwh.items():
            daily_kwh[day] = daily_kwh.get(day, 0.0) + value

    return values, daily_kwh


def create_forecast(config: ForecastSolar):
    def updater():
        values, daily_kwh = fetch_forecast(config.configuration)
        return ForecastState(forecast_values=values, daily_kwh=daily_kwh)
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=ForecastSolar)
