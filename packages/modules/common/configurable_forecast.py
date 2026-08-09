import logging
from dataclasses import asdict
from datetime import datetime, timedelta
from importlib import import_module
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
        # Store reference to forecast.get for persistent state across re-initialization (same pattern as EP modules)
        self.get = data.data.optional_data.data.forecast.get

    def _is_config_complete(self) -> bool:
        """Check if forecast provider configuration has all required fields.
        
        Calls the provider module's is_configuration_complete() function if available.
        Falls back to True (assuming complete) if the function is not found.
        """
        try:
            provider_type = self.config.type
            config = self.config.configuration
            
            # Dynamically import the provider module and call its validation function
            module_name = f"modules.forecast.{provider_type}.forecast"
            provider_module = import_module(module_name)
            
            # Call the validation function if it exists
            if hasattr(provider_module, "is_configuration_complete"):
                return provider_module.is_configuration_complete(config)
            
            # If validation function doesn't exist, assume config is complete
            return True
        except Exception as e:
            log.warning(f"Error checking forecast config completeness: {e}")
            # On error, assume incomplete to be safe
            return False

    def _publish_forecast_fault(self, level: FaultStateLevel, message: str) -> None:
        data.data.optional_data.data.forecast.get.fault_state = level.value
        data.data.optional_data.data.forecast.get.fault_str = message
        Pub().pub("openWB/set/optional/forecast/get/fault_state", level.value)
        Pub().pub("openWB/set/optional/forecast/get/fault_str", message)

    def _is_update_due(self) -> bool:
        """Check if a forecast update is due.
        
        Returns False immediately if configuration is incomplete (prevents API calls before config is saved).
        Otherwise checks if the scheduled update time has been reached.
        """
        if not self._is_config_complete():
            return False
        
        return self.get.next_query_time is None or self.get.next_query_time == 0 or self.get.next_query_time <= timecheck.create_timestamp()

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
        self.get.next_query_time = int(next_query_time.timestamp())
        Pub().pub("openWB/set/optional/forecast/get/next_query_time", self.get.next_query_time)

    def _set_retry_query_time(self, minutes: int = FORECAST_RETRY_MINUTES) -> None:
        self.get.next_query_time = int((datetime.now() + timedelta(minutes=minutes)).timestamp())
        Pub().pub("openWB/set/optional/forecast/get/next_query_time", self.get.next_query_time)

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
            now_ts = int(datetime.now().timestamp())
            data.data.optional_data.data.forecast.get.last_update_time = now_ts
            Pub().pub("openWB/set/optional/forecast/get/last_update_time", now_ts)
            log.info(
                "Forecast update finished (provider=%s, values=%s, next_query_time=%s)",
                self.config.type,
                len(state.forecast_values or {}),
                self.get.next_query_time,
            )
        except Exception as e:
            error_str = str(e)
            if "429" in error_str:
                # Rate limited providers should wait until the next planned schedule slot.
                self._set_next_query_time_by_schedule()
                self._publish_forecast_fault(
                    FaultStateLevel.WARNING,
                    "Forecast API rate limit reached (HTTP 429). Waiting for next scheduled update.",
                )
            elif "Missing required" in error_str or "required forecast config field" in error_str.lower():
                # Configuration is incomplete; don't retry automatically.
                # Next attempt will be on next scheduled time or manual trigger.
                self._set_next_query_time_by_schedule()
                self._publish_forecast_fault(
                    FaultStateLevel.WARNING,
                    f"Forecast configuration incomplete: {error_str}. Please configure all required fields.",
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
