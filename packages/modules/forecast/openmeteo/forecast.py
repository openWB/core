from datetime import datetime
import logging
from typing import Any, Dict
from zoneinfo import ZoneInfo

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ForecastState

from modules.forecast.openmeteo.config import OpenMeteoForecast, OpenMeteoForecastConfiguration

OPEN_METEO_FORECAST_HOURS = 48
log = logging.getLogger("forecast")


def _require(value, field_name: str):
    if value is None:
        raise ValueError(f"Missing required forecast config field: {field_name}")
    if isinstance(value, str) and value.strip() == "":
        raise ValueError(f"Missing required forecast config field: {field_name}")
    return value


def fetch_forecast(config: OpenMeteoForecastConfiguration) -> Dict[str, float]:
    latitude = _require(config.latitude, "latitude")
    longitude = _require(config.longitude, "longitude")
    timezone = _require(config.timezone, "timezone")
    peak_power_kw = float(_require(config.peak_power_kw, "peak_power_kw"))
    if peak_power_kw <= 0:
        raise ValueError("Missing required forecast config field: peak_power_kw")
    system_loss = float(_require(config.system_loss, "system_loss"))
    irradiance_to_power_factor = float(_require(config.irradiance_to_power_factor, "irradiance_to_power_factor"))
    if irradiance_to_power_factor <= 0:
        raise ValueError("Missing required forecast config field: irradiance_to_power_factor")

    if config.strings:
        string_configs: list[dict[str, Any]] = config.strings
    else:
        string_configs = [{
            "peak_power_kw": peak_power_kw,
            "tilt": config.tilt,
            "azimuth": config.azimuth,
        }]
    if len(string_configs) > 6:
        string_configs = string_configs[:6]

    log.info(
        "Open-Meteo forecast fetch started (strings=%s, timezone=%s, horizon_hours=%s)",
        len(string_configs),
        timezone,
        OPEN_METEO_FORECAST_HOURS,
    )

    values: Dict[str, float] = {}
    for string_config in string_configs:
        string_peak_power_kw = float(_require(string_config.get("peak_power_kw"), "strings[].peak_power_kw"))
        if string_peak_power_kw <= 0:
            raise ValueError("Missing required forecast config field: strings[].peak_power_kw")

        string_tilt = float(_require(string_config.get("tilt"), "strings[].tilt"))
        string_azimuth = float(_require(string_config.get("azimuth"), "strings[].azimuth"))

        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={latitude}"
            f"&longitude={longitude}"
            "&hourly=global_tilted_irradiance"
            f"&timezone={timezone}"
            f"&tilt={string_tilt}"
            f"&azimuth={string_azimuth}"
        )

        response = req.get_http_session().get(url, timeout=(2, 6)).json()
        hourly = response.get("hourly", {})
        times = hourly.get("time", [])
        radiation = hourly.get("global_tilted_irradiance", [])
        log.info(
            "Open-Meteo response received (times=%s, irradiance_values=%s)",
            len(times),
            len(radiation),
        )
        for timestamp, value in zip(times[:OPEN_METEO_FORECAST_HOURS], radiation[:OPEN_METEO_FORECAST_HOURS]):
            if value is None:
                continue
            estimated_power_w = max(
                0.0,
                string_peak_power_kw * 1000.0 * (float(value) / 1000.0) * irradiance_to_power_factor
                * (1.0 - system_loss)
            )
            timestamp_key = str(__parse_timestamp(timestamp, timezone))
            values[timestamp_key] = values.get(timestamp_key, 0.0) + estimated_power_w
    log.info("Open-Meteo forecast fetch finished (merged_values=%s)", len(values))
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
