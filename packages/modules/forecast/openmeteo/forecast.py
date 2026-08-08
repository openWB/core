from datetime import datetime
from typing import Dict
from zoneinfo import ZoneInfo

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ForecastState

from modules.forecast.openmeteo.config import OpenMeteoForecast, OpenMeteoForecastConfiguration

OPEN_METEO_FORECAST_HOURS = 48


def _require(value, field_name: str):
    if value is None:
        raise ValueError(f"Missing required forecast config field: {field_name}")
    if isinstance(value, str) and value.strip() == "":
        raise ValueError(f"Missing required forecast config field: {field_name}")
    if isinstance(value, (int, float)) and float(value) == 0.0:
        raise ValueError(f"Missing required forecast config field: {field_name}")
    return value


def fetch_forecast(config: OpenMeteoForecastConfiguration) -> Dict[str, float]:
    latitude = _require(config.latitude, "latitude")
    longitude = _require(config.longitude, "longitude")
    timezone = _require(config.timezone, "timezone")
    peak_power_kw = _require(config.peak_power_kw, "peak_power_kw")
    system_loss = _require(config.system_loss, "system_loss")
    irradiance_to_power_factor = _require(config.irradiance_to_power_factor, "irradiance_to_power_factor")

    values: Dict[str, float] = {}
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
        "&hourly=shortwave_radiation"
        f"&timezone={timezone}"
    )

    response = req.get_http_session().get(url, timeout=(2, 6)).json()
    hourly = response.get("hourly", {})
    times = hourly.get("time", [])
    radiation = hourly.get("shortwave_radiation", [])
    for timestamp, value in zip(times[:OPEN_METEO_FORECAST_HOURS], radiation[:OPEN_METEO_FORECAST_HOURS]):
        if value is None:
            continue
        estimated_power_w = max(
            0.0,
            float(peak_power_kw) * 1000.0 * (float(value) / 1000.0) * float(irradiance_to_power_factor)
            * (1.0 - float(system_loss))
        )
        timestamp_key = str(__parse_timestamp(timestamp, timezone))
        values[timestamp_key] = estimated_power_w
    return values


def __parse_timestamp(value: str, timezone_name: str) -> int:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo(timezone_name))
    return int(parsed.timestamp())


def create_forecast(config: OpenMeteoForecast):
    def updater():
        return ForecastState(forecast_values=fetch_forecast(config.configuration))
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=OpenMeteoForecast)
