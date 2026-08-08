from datetime import datetime
import logging
from typing import Any, Dict
from requests import HTTPError

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ForecastState

from modules.forecast.forecastsolar.config import ForecastSolar, ForecastSolarConfiguration


log = logging.getLogger(__name__)


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


def fetch_forecast(config: ForecastSolarConfiguration) -> Dict[str, float]:
    latitude = config.latitude if config.latitude is not None else 52.52
    longitude = config.longitude if config.longitude is not None else 13.405
    peak_power_kw = config.peak_power_kw if config.peak_power_kw is not None else 5.0
    azimuth = config.azimuth if config.azimuth is not None else 180.0
    tilt = config.tilt if config.tilt is not None else 35.0
    loss = config.loss if config.loss is not None else 14.0
    horizon = config.horizon if config.horizon is not None else "0"

    string_configs: list[dict[str, Any]] = config.strings if config.strings else [{
        "peak_power_kw": peak_power_kw,
        "azimuth": azimuth,
        "tilt": tilt,
        "loss": loss,
        "horizon": horizon,
    }]
    if len(string_configs) > 6:
        string_configs = string_configs[:6]
    values: Dict[str, float] = {}
    for string_config in string_configs:
        string_peak_power_kw = string_config.get("peak_power_kw") if string_config.get("peak_power_kw") is not None else peak_power_kw
        string_azimuth = string_config.get("azimuth") if string_config.get("azimuth") is not None else azimuth
        string_tilt = string_config.get("tilt") if string_config.get("tilt") is not None else tilt
        string_loss = string_config.get("loss") if string_config.get("loss") is not None else loss
        string_horizon = string_config.get("horizon") if string_config.get("horizon") is not None else horizon

        url = (
            "https://api.forecast.solar/estimate/watts"
            f"?lat={latitude}"
            f"&lon={longitude}"
            f"&dec={string_peak_power_kw}"
            f"&az={string_azimuth}"
            f"&tilt={string_tilt}"
            f"&loss={string_loss}"
            f"&horizon={string_horizon}"
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
        for timestamp, value in response.items():
            if value is None:
                continue
            timestamp_key = str(int(datetime.fromisoformat(timestamp).timestamp()))
            values[timestamp_key] = values.get(timestamp_key, 0.0) + float(value)
    return values


def create_forecast(config: ForecastSolar):
    def updater():
        return ForecastState(forecast_values=fetch_forecast(config.configuration))
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=ForecastSolar)
