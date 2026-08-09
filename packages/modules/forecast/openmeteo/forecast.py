from datetime import datetime
import logging
from typing import Dict
from zoneinfo import ZoneInfo

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ForecastState

from modules.forecast.openmeteo.config import OpenMeteoForecast, OpenMeteoForecastConfiguration

OPEN_METEO_FORECAST_HOURS = 48
log = logging.getLogger("forecast")


def is_configuration_complete(config: OpenMeteoForecastConfiguration) -> bool:
    """Check if Open-Meteo configuration has all required fields."""
    strings = getattr(config, "strings", None)
    return isinstance(strings, list) and len(strings) > 0


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
    system_loss = float(config.system_loss if config.system_loss is not None else 0.14)

    string_configs_raw = _require(config.strings, "strings")
    if not isinstance(string_configs_raw, list) or len(string_configs_raw) == 0:
        raise ValueError("Missing required forecast config field: strings")
    string_configs = string_configs_raw[:6]

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
            # STC: peak power is rated at 1000 W/m²; scale linearly with irradiance and apply losses
            estimated_power_w = max(
                0.0,
                string_peak_power_kw * 1000.0 * (float(value) / 1000.0) * (1.0 - system_loss)
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
