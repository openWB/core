from datetime import datetime
import logging
from typing import Dict, Tuple
from requests import HTTPError

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ForecastState

from modules.forecast.forecast_solar.config import ForecastSolar, ForecastSolarConfiguration


log = logging.getLogger("forecast")


def is_configuration_complete(config: ForecastSolarConfiguration) -> bool:
    """Prüfe, ob die Forecast.Solar-Konfiguration alle erforderlichen Felder hat."""
    return len(config.strings) > 0


def _require(value, field_name: str):
    if (
        value is None
        or (isinstance(value, str) and value.strip() == "")
        or (isinstance(value, list) and len(value) == 0)
    ):
        raise ValueError(f"Missing required forecast config field: {field_name}")
    return value


def _parse_forecast_solar_response(payload: Dict) -> Dict[str, float]:
    # Vorhersage-API-Endpunkte ("estimate") geben das Ergebnis direkt als flaches {Zeitstempel: Wert} Dict zurück.
    watts_raw = payload.get("result") if isinstance(payload, dict) else None
    values: Dict[str, float] = {}
    if isinstance(watts_raw, dict):
        for timestamp, value in watts_raw.items():
            if value is None:
                continue
            timestamp_key = str(int(datetime.fromisoformat(timestamp).timestamp()))
            values[timestamp_key] = float(value)
    return values


def fetch_forecast(config: ForecastSolarConfiguration) -> Tuple[Dict[str, float], Dict[str, float]]:
    latitude = _require(config.latitude, "latitude")
    longitude = _require(config.longitude, "longitude")
    string_configs = _require(config.strings, "strings")
    if len(string_configs) > 6:
        log.warning(f"Es wurden {len(string_configs)} Strings konfiguriert. Es werden nur die ersten 6 verwendet.")
        string_configs = string_configs[:6]

    log.info(f"Forecast.Solar-Abruf gestartet (Strings={len(string_configs)})")

    values: Dict[str, float] = {}
    daily_kwh: Dict[str, float] = {}

    for string_config in string_configs:
        peak_power_kw = float(_require(string_config.get("peak_power_kw"), "strings[].peak_power_kw"))
        if peak_power_kw <= 0:
            raise ValueError("Missing required forecast config field: strings[].peak_power_kw")
        azimuth = _require(string_config.get("azimuth"), "strings[].azimuth")
        tilt = _require(string_config.get("tilt"), "strings[].tilt")

        url = (
            f"https://api.forecast.solar/{config.api_key}/estimate/watts"
            if config.api_key and config.api_key.strip()
            else "https://api.forecast.solar/estimate/watts"
        )
        url += (
            f"/{latitude}"
            f"/{longitude}"
            f"/{tilt}"
            f"/{azimuth}"
            f"/{peak_power_kw}"
        )
        try:
            response_obj = req.get_http_session().get(url, timeout=(2, 6))
            response_obj.raise_for_status()
        except HTTPError as e:
            response = e.response
            if response is not None and response.status_code == 429:
                retry_at = response.headers.get("X-Ratelimit-Retry-At")
                remaining = response.headers.get("X-Ratelimit-Remaining")
                limit = response.headers.get("X-Ratelimit-Limit")
                period = response.headers.get("X-Ratelimit-Period")
                log.warning(f"Forecast.Solar rate limit hit for {url}: "
                            f"remaining={remaining} limit={limit} period={period} retry_at={retry_at}")
            raise

        response = response_obj.json()
        log.debug(f"Forecast.Solar Antwort für String {string_config.get('name')}: {response}")
        string_values = _parse_forecast_solar_response(response)
        for timestamp, value in string_values.items():
            values[timestamp] = values.get(timestamp, 0.0) + value

    # Die genutzte /estimate/watts-Route liefert grundsätzlich keine vorab aggregierten
    # Tageswerte (weder mit noch ohne API-Key), daher werden sie aus den Stundenwerten berechnet.
    daily_kwh = _calculate_daily_kwh_from_values(values)

    log.info(f"Forecast.Solar-Abruf beendet (Werte={len(values)}, Tage={len(daily_kwh)})")
    return values, daily_kwh


def _calculate_daily_kwh_from_values(values: Dict[str, float]) -> Dict[str, float]:
    """Berechne tägliche Energiewerte aus stündlichen Leistungswerten."""
    points: list[tuple[datetime, float]] = []
    for timestamp, value in values.items():
        try:
            points.append((datetime.fromtimestamp(int(timestamp)), float(value)))
        except (TypeError, ValueError):
            continue

    if not points:
        return {}

    points.sort(key=lambda item: item[0])
    deltas = [
        int((points[index + 1][0] - points[index][0]).total_seconds())
        for index in range(len(points) - 1)
        if 0 < int((points[index + 1][0] - points[index][0]).total_seconds()) <= 21600
    ]
    fallback_step_seconds = min(deltas) if deltas else 3600

    daily_wh: Dict[str, float] = {}
    for index, (timestamp, power_w) in enumerate(points):
        if index + 1 < len(points):
            step_seconds = int((points[index + 1][0] - timestamp).total_seconds())
            if step_seconds <= 0 or step_seconds > 21600:
                step_seconds = fallback_step_seconds
        else:
            step_seconds = fallback_step_seconds
        date_key = timestamp.date().isoformat()
        daily_wh[date_key] = daily_wh.get(date_key, 0.0) + max(0.0, power_w) * (step_seconds / 3600.0)

    return {date_key: energy_wh / 1000.0 for date_key, energy_wh in daily_wh.items()}


def create_forecast(config: ForecastSolar):
    def updater():
        values, daily_kwh = fetch_forecast(config.configuration)
        return ForecastState(forecast_values=values, daily_kwh=daily_kwh)
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=ForecastSolar)
