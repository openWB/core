from datetime import datetime
from typing import Any, Dict
from zoneinfo import ZoneInfo

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ForecastState

from modules.forecast.openmeteo.config import OpenMeteoForecast, OpenMeteoForecastConfiguration


def fetch_forecast(config: OpenMeteoForecastConfiguration) -> Dict[str, float]:
    latitude = config.latitude if config.latitude is not None else 52.52
    longitude = config.longitude if config.longitude is not None else 13.405
    timezone = config.timezone if config.timezone is not None else "Europe/Berlin"
    forecast_hours = config.forecast_hours if config.forecast_hours is not None else 24
    peak_power_kw = config.peak_power_kw if config.peak_power_kw is not None else 5.0
    system_loss = config.system_loss if config.system_loss is not None else 0.15
    irradiance_to_power_factor = (
        config.irradiance_to_power_factor if config.irradiance_to_power_factor is not None else 1.0
    )

    string_configs: list[dict[str, Any]] = config.strings if config.strings else [{"peak_power_kw": peak_power_kw}]
    if len(string_configs) > 6:
        string_configs = string_configs[:6]
    values: Dict[str, float] = {}
    for string_config in string_configs:
        string_peak_power_kw = (
            string_config.get("peak_power_kw") if string_config.get("peak_power_kw") is not None else peak_power_kw
        )
        tilt = string_config.get("tilt")
        azimuth = string_config.get("azimuth")
        hourly_field = "global_tilted_irradiance" if tilt is not None or azimuth is not None else "shortwave_radiation"

        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={latitude}"
            f"&longitude={longitude}"
            f"&hourly={hourly_field}"
            f"&timezone={timezone}"
        )
        if tilt is not None:
            url += f"&tilt={tilt}"
        if azimuth is not None:
            url += f"&azimuth={azimuth}"

        response = req.get_http_session().get(url, timeout=(2, 6)).json()
        hourly = response.get("hourly", {})
        times = hourly.get("time", [])
        radiation = hourly.get(hourly_field, [])
        for timestamp, value in zip(times[:forecast_hours], radiation[:forecast_hours]):
            if value is None:
                continue
            estimated_power_w = max(
                0.0,
                float(string_peak_power_kw) * 1000.0 * (float(value) / 1000.0) * float(irradiance_to_power_factor)
                * (1.0 - float(system_loss))
            )
            timestamp_key = str(__parse_timestamp(timestamp, timezone))
            values[timestamp_key] = values.get(timestamp_key, 0.0) + estimated_power_w
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
