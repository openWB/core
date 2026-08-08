from datetime import datetime
from typing import Any, Dict

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ForecastState

from modules.forecast.pvnode.config import PvNode, PvNodeConfiguration


def _normalize_timestamp(value: Any) -> int | None:
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


def fetch_forecast(config: PvNodeConfiguration) -> Dict[str, float]:
    latitude = config.latitude if config.latitude is not None else 52.52
    longitude = config.longitude if config.longitude is not None else 13.405
    peak_power_kw = config.peak_power_kw if config.peak_power_kw is not None else 5.0
    system_loss = config.system_loss if config.system_loss is not None else 0.1
    plant_id = config.plant_id if config.plant_id is not None else ""

    path = f"/v2/forecast/{plant_id}" if plant_id else "/v2/forecast"
    url = f"https://api.pvnode.com{path}"
    headers = {"Authorization": f"Bearer {config.api_key}"} if config.api_key else {}
    response = req.get_http_session().get(url, headers=headers, timeout=(2, 6)).json()
    values: Dict[str, float] = {}

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
            value = entry.get("pv_power") or entry.get("power_kw") or entry.get("power") or entry.get("value")
            if timestamp is None or value is None:
                continue
            numeric_value = float(value)
            if entry.get("pv_power") is not None and numeric_value > 1000.0:
                estimated_power_w = max(0.0, numeric_value)
            elif entry.get("pv_power") is not None:
                estimated_power_w = max(0.0, numeric_value)
            else:
                estimated_power_w = max(
                    0.0,
                    numeric_value * float(peak_power_kw) / 100.0 * (1.0 - float(system_loss)) * 1000.0
                )
            values[str(timestamp)] = estimated_power_w
    elif isinstance(payload, dict):
        for key, value in payload.items():
            timestamp = _normalize_timestamp(key)
            if timestamp is None or value is None:
                continue
            numeric_value = float(value)
            if isinstance(value, (int, float)) and numeric_value > 1000.0:
                estimated_power_w = max(0.0, numeric_value)
            else:
                estimated_power_w = max(
                    0.0,
                    numeric_value * float(peak_power_kw) / 100.0 * (1.0 - float(system_loss)) * 1000.0
                )
            values[str(timestamp)] = estimated_power_w

    return values


def create_forecast(config: PvNode):
    def updater():
        return ForecastState(forecast_values=fetch_forecast(config.configuration))
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=PvNode)
