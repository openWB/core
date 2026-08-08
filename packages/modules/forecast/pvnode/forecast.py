from datetime import datetime
from typing import Any, Dict, Tuple

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ForecastState

from modules.forecast.pvnode.config import PvNode, PvNodeConfiguration


def _require(value, field_name: str):
    if value is None:
        raise ValueError(f"Missing required forecast config field: {field_name}")
    if isinstance(value, str) and value.strip() == "":
        raise ValueError(f"Missing required forecast config field: {field_name}")
    if isinstance(value, (int, float)) and float(value) == 0.0:
        raise ValueError(f"Missing required forecast config field: {field_name}")
    return value


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


def fetch_forecast(config: PvNodeConfiguration) -> Tuple[Dict[str, float], Dict[str, float]]:
    peak_power_kw = _require(config.peak_power_kw, "peak_power_kw")
    system_loss = _require(config.system_loss, "system_loss")
    plant_id = _require(config.plant_id, "plant_id")

    path = f"/v2/forecast/{plant_id}"
    url = f"https://api.pvnode.com{path}"
    api_key = _require(config.api_key, "api_key")
    headers = {"Authorization": f"Bearer {api_key}"}
    response = req.get_http_session().get(url, headers=headers, timeout=(2, 6)).json()
    values: Dict[str, float] = {}
    daily_kwh: Dict[str, float] = {}

    daily_payload = response.get("daily")
    if isinstance(daily_payload, list):
        for entry in daily_payload:
            if not isinstance(entry, dict):
                continue
            date_key = entry.get("date")
            energy_kwh = entry.get("pv_energy_kwh")
            if date_key is None or energy_kwh is None:
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

    return values, daily_kwh


def create_forecast(config: PvNode):
    def updater():
        values, daily_kwh = fetch_forecast(config.configuration)
        return ForecastState(forecast_values=values, daily_kwh=daily_kwh)
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=PvNode)
