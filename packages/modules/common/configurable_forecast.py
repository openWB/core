import logging
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Callable, Generic, Optional, TypeVar

from control import data
from control.optional_data import OptionalData
from helpermodules import timecheck
from helpermodules.constants import NO_ERROR
from helpermodules.pub import Pub
from modules.common import store
from modules.common.component_state import ForecastState
from modules.common.fault_state_level import FaultStateLevel

T_FORECAST_CONFIG = TypeVar("T_FORECAST_CONFIG")
log = logging.getLogger("forecast")
DEFAULT_FORECAST_UPDATE_HOURS = [5, 8, 11, 14, 17, 20]
FORECAST_RETRY_MINUTES = 15


class ConfigurableForecast(Generic[T_FORECAST_CONFIG]):
    def __init__(self,
                 config: T_FORECAST_CONFIG,
                 component_initializer: Callable[[T_FORECAST_CONFIG], ForecastState]) -> None:
        self.config = config
        self.store = store.get_forecast_value_store()
        self._component_updater = component_initializer(config)
        self.update_hours = DEFAULT_FORECAST_UPDATE_HOURS
        self.next_query_time: Optional[int] = None

    def _publish_forecast_fault(self, level: FaultStateLevel, message: str) -> None:
        data.data.optional_data.data.forecast.get.fault_state = level.value
        data.data.optional_data.data.forecast.get.fault_str = message
        Pub().pub("openWB/set/optional/forecast/get/fault_state", level.value)
        Pub().pub("openWB/set/optional/forecast/get/fault_str", message)

    def _is_update_due(self) -> bool:
        return self.next_query_time is None or self.next_query_time <= timecheck.create_timestamp()

    def _is_force_update_requested(self) -> bool:
        return bool(data.data.optional_data.data.forecast.get.force_update)

    def _clear_force_update_request(self) -> None:
        if data.data.optional_data.data.forecast.get.force_update:
            data.data.optional_data.data.forecast.get.force_update = False
            Pub().pub("openWB/set/optional/forecast/get/force_update", False)

    def _set_next_query_time_by_schedule(self) -> None:
        now = datetime.now()
        current_hour = now.hour
        next_hour = min([hour for hour in self.update_hours if hour > current_hour], default=self.update_hours[0])
        day_offset = 0 if next_hour > current_hour else 1
        next_query_time = now.replace(hour=next_hour, minute=0, second=0, microsecond=0) + timedelta(days=day_offset)
        self.next_query_time = int(next_query_time.timestamp())
        Pub().pub("openWB/set/optional/forecast/get/next_query_time", self.next_query_time)

    def _set_retry_query_time(self, minutes: int = FORECAST_RETRY_MINUTES) -> None:
        self.next_query_time = int((datetime.now() + timedelta(minutes=minutes)).timestamp())
        Pub().pub("openWB/set/optional/forecast/get/next_query_time", self.next_query_time)

    def update(self) -> None:
        force_update = self._is_force_update_requested()
        if not force_update and not self._is_update_due():
            return
        try:
            trigger_mode = "manual" if force_update else "scheduled"
            log.info("Forecast update started (provider=%s, trigger=%s)", self.config.type, trigger_mode)
            state = self._component_updater()
            self.store.set(state)
            self.store.update()
            self._set_next_query_time_by_schedule()
            self._publish_forecast_fault(FaultStateLevel.NO_ERROR, NO_ERROR)
            data.data.optional_data.data.forecast.configured = True
            data.data.optional_data.data.forecast.provider = asdict(self.config)
            Pub().pub("openWB/set/optional/forecast/current", state.forecast_values)
            log.info(
                "Forecast update finished (provider=%s, values=%s, next_query_time=%s)",
                self.config.type,
                len(state.forecast_values or {}),
                self.next_query_time,
            )
        except Exception as e:
            if "429" in str(e):
                # Rate limited providers should wait until the next planned schedule slot.
                self._set_next_query_time_by_schedule()
                self._publish_forecast_fault(
                    FaultStateLevel.WARNING,
                    "Forecast API rate limit reached (HTTP 429). Waiting for next scheduled update.",
                )
            else:
                self._set_retry_query_time()
                self._publish_forecast_fault(
                    FaultStateLevel.WARNING,
                    "Forecast update failed. Retry scheduled in 15 minutes.",
                )
            log.exception(f"Fehler beim Aktualisieren der Forecast-Daten {e}")
        finally:
            self._clear_force_update_request()


class ConfigurableForecastProvider(ConfigurableForecast[T_FORECAST_CONFIG]):
    def __init__(self,
                 config: T_FORECAST_CONFIG,
                 component_initializer: Callable[[T_FORECAST_CONFIG], ForecastState]) -> None:
        super().__init__(config, component_initializer)
        self._optional_data = OptionalData()
