from datetime import datetime
from typing import Dict

from control import data
from helpermodules.pub import Pub
from modules.common.component_state import ForecastState
from modules.common.store import ValueStore
from modules.common.store._api import LoggingValueStore
from modules.common.store._broker import pub_to_broker
import logging


log = logging.getLogger(__name__)


def _parse_forecast_timestamp(timestamp: str) -> datetime | None:
    try:
        if timestamp.isdigit():
            return datetime.fromtimestamp(int(timestamp))
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _calculate_daily_kwh(values: Dict[str, float]) -> Dict[str, float]:
    points: list[tuple[datetime, float]] = []
    for timestamp, value in values.items():
        parsed_timestamp = _parse_forecast_timestamp(timestamp)
        if parsed_timestamp is None:
            continue
        points.append((parsed_timestamp, float(value)))

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


class ForecastValueStore(ValueStore[ForecastState]):
    def __init__(self):
        pass

    def set(self, state: ForecastState) -> None:
        self.state = state

    def update(self):
        values = self.state.forecast_values or {}
        daily_kwh = _calculate_daily_kwh(values)
        data.data.optional_data.data.forecast.get.values = values
        data.data.optional_data.data.forecast.get.daily_kwh = daily_kwh
        pub_to_broker("openWB/set/optional/forecast/get/values", values)
        pub_to_broker("openWB/set/optional/forecast/get/daily_kwh", daily_kwh)
        Pub().pub("openWB/optional/forecast/current", values)
        log.debug(f"published forecast values to MQTT having {len(values)} entries and {len(daily_kwh)} day totals")


def get_forecast_value_store() -> ValueStore[ForecastState]:
    return LoggingValueStore(ForecastValueStore())
