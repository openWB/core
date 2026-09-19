import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from control import data
from modules.common.component_state import ForecastState
from modules.common.store import ValueStore
from modules.common.store._api import LoggingValueStore
from modules.common.store._broker import pub_to_broker


log = logging.getLogger(__name__)


def _parse_forecast_timestamp(timestamp: str) -> Optional[datetime]:
    try:
        if timestamp.isdigit():
            return datetime.fromtimestamp(int(timestamp))
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _filter_values_for_date(values: Dict[str, float], target_date) -> Dict[str, float]:
    day_values: Dict[str, float] = {}
    for timestamp, value in values.items():
        parsed_timestamp = _parse_forecast_timestamp(timestamp)
        if parsed_timestamp is None:
            continue
        if parsed_timestamp.date() == target_date:
            day_values[timestamp] = float(value)
    return day_values


class ForecastValueStore(ValueStore[ForecastState]):
    def __init__(self):
        pass

    def set(self, state: ForecastState) -> None:
        self.state = state

    def update(self):
        values = self.state.forecast_values or {}
        daily_kwh = self.state.daily_kwh or {}
        today_date = datetime.now().date()
        tomorrow_date = datetime.now().date() + timedelta(days=1)
        today_values = _filter_values_for_date(values, today_date)
        tomorrow_values = _filter_values_for_date(values, tomorrow_date)
        today_kwh = float(daily_kwh.get(today_date.isoformat(), 0.0))
        tomorrow_kwh = float(daily_kwh.get(tomorrow_date.isoformat(), 0.0))
        data.data.optional_data.data.forecast.get.values = values
        data.data.optional_data.data.forecast.get.today_values = today_values
        data.data.optional_data.data.forecast.get.tomorrow_values = tomorrow_values
        data.data.optional_data.data.forecast.get.daily_kwh = daily_kwh
        data.data.optional_data.data.forecast.get.today_kwh = today_kwh
        data.data.optional_data.data.forecast.get.tomorrow_kwh = tomorrow_kwh
        pub_to_broker("openWB/set/optional/forecast/get/values", values)
        pub_to_broker("openWB/set/optional/forecast/get/today_values", today_values)
        pub_to_broker("openWB/set/optional/forecast/get/tomorrow_values", tomorrow_values)
        pub_to_broker("openWB/set/optional/forecast/get/daily_kwh", daily_kwh)
        pub_to_broker("openWB/set/optional/forecast/get/today_kwh", today_kwh)
        pub_to_broker("openWB/set/optional/forecast/get/tomorrow_kwh", tomorrow_kwh)
        log.debug(
            "Prognosewerte an MQTT veröffentlicht mit %s Einträgen, %s Tagestotalen, %s Einträgen heute und"
            " %s Einträgen morgen",
            len(values),
            len(daily_kwh),
            len(today_values),
            len(tomorrow_values),
        )


def get_forecast_value_store() -> ValueStore[ForecastState]:
    return LoggingValueStore(ForecastValueStore())
