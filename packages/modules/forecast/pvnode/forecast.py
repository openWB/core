from datetime import datetime
import logging
from typing import Any, Dict, Optional, Tuple

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ForecastState

from modules.forecast.pvnode.config import PvNode, PvNodeConfiguration


log = logging.getLogger("forecast")


def is_configuration_complete(config: PvNodeConfiguration) -> bool:
    """Prüfe, ob die PVNode-Konfiguration alle erforderlichen Felder hat."""
    return (config.plant_id is not None and len(config.plant_id.strip()) > 0
            and config.api_key is not None and len(config.api_key.strip()) > 0)


def _require(value, field_name: str):
    if value is None or isinstance(value, str) and len(value.strip()) == 0:
        raise ValueError(f"Missing required forecast config field: {field_name}")
    return value


def _normalize_timestamp(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if text.isdigit():
            return int(text)
        try:
            return int(datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp())
        except ValueError:
            return None
    return None


def _mask_identifier(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return "*" * len(value)
    return f"{'*' * (len(value) - 4)}{value[-4:]}"


def fetch_forecast(config: PvNodeConfiguration) -> Tuple[Dict[str, float], Dict[str, float]]:
    plant_id = _require(config.plant_id, "plant_id")
    masked_plant_id = _mask_identifier(str(plant_id))
    log.info(f"PVNode-Abruf gestartet (plant_id={masked_plant_id})")

    path = f"/v2/forecast/{plant_id}"
    url = f"https://api.pvnode.com{path}"
    api_key = _require(config.api_key, "api_key")
    headers = {"Authorization": f"Bearer {api_key}"}
    response = req.get_http_session().get(url, headers=headers, timeout=(2, 6)).json()
    log.debug(f"PVNode-Antwort erhalten: {response}")
    values: Dict[str, float] = {}
    daily_kwh: Dict[str, float] = {}

    daily_payload = response.get("daily")
    if isinstance(daily_payload, list):
        for entry in daily_payload:
            if (
                not isinstance(entry, dict) or
                (date_key := entry.get("date")) is None or
                (energy_kwh := entry.get("pv_energy_kwh")) is None
            ):
                continue
            daily_kwh[str(date_key)] = float(energy_kwh)

    payload = response.get("values")
    if payload is None:
        payload = response.get("data")
    if payload is None:
        payload = response.get("forecast") or response.get("forecasts") or []

    if isinstance(payload, list):
        for entry in payload:
            if not isinstance(entry, dict):
                continue
            timestamp = _normalize_timestamp(
                entry.get("timestamp") or entry.get("period_end") or entry.get("period_start")
            )
            power_w = entry.get("pv_power")
            if power_w is None and (power_kw := entry.get("power_kw")) is not None:
                power_w = float(power_kw) * 1000.0
            if power_w is None:
                power_w = entry.get("power")
            if power_w is None:
                power_w = entry.get("value")
            if timestamp is None or power_w is None:
                continue
            estimated_power_w = max(0.0, float(power_w))
            values[str(timestamp)] = estimated_power_w
    elif isinstance(payload, dict):
        for key, value in payload.items():
            timestamp = _normalize_timestamp(key)
            if timestamp is None or value is None:
                continue
            estimated_power_w = max(0.0, float(value))
            values[str(timestamp)] = estimated_power_w

    log.info(f"PVNode-Abruf beendet (Werte={len(values)}, Tage={len(daily_kwh)})")

    return values, daily_kwh


def create_forecast(config: PvNode):
    def updater():
        values, daily_kwh = fetch_forecast(config.configuration)
        return ForecastState(forecast_values=values, daily_kwh=daily_kwh)
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=PvNode)
