import logging
from dataclasses import asdict
from datetime import datetime, timedelta
from importlib import import_module
from typing import Callable, Generic, Optional, TypeVar

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
        
        # Falls next_query_time nicht gesetzt ist, berechne die nächste geplante Aktualisierungszeit
        # Dies verhindert sofortige Aktualisierungen, wenn ein Anbieter erstmals erstellt wird
        if self.get.next_query_time is None or self.get.next_query_time == 0:
            self._set_next_query_time_by_schedule()

    @property
    def get(self):
        """Gibt immer die aktuelle Singleton-Prognose.get aus der globalen SubData-Instanz zurück.
        
        SubData.optional_data ist die globale Singleton, die MQTT-Nachrichten aktualisieren.
        Dies stellt sicher, dass wir immer den aktuellen Status haben, keine veraltete Referenz.
        """
        from helpermodules import subdata
        return subdata.SubData.optional_data.data.forecast.get

    def _is_config_complete(self) -> bool:
        """Prüfe, ob die Prognose-Anbieter-Konfiguration alle erforderlichen Felder hat.
        
        Ruft die is_configuration_complete()-Funktion des Anbietermoduls auf, falls vorhanden.
        Fällt auf True zurück (nimmt Vollständigkeit an), wenn die Funktion nicht gefunden wird.
        """
        try:
            provider_type = self.config.type
            config = self.config.configuration
            
            # Importiere das Anbietermodul dynamisch und rufe seine Validierungsfunktion auf
            module_name = f"modules.forecast.{provider_type}.forecast"
            provider_module = import_module(module_name)
            
            # Rufe die Validierungsfunktion auf, falls vorhanden
            if hasattr(provider_module, "is_configuration_complete"):
                return provider_module.is_configuration_complete(config)
            
            # Wenn Validierungsfunktion nicht vorhanden, nimm an, dass Konfiguration vollständig ist
            return True
        except Exception as e:
            log.warning(f"Fehler beim Prüfen der Prognose-Konfigurationsvollständigkeit: {e}")
            # On error, assume incomplete to be safe
            return False

    def _publish_forecast_fault(self, level: FaultStateLevel, message: str) -> None:
        self.get.fault_state = level.value
        self.get.fault_str = message
        Pub().pub("openWB/set/optional/forecast/get/fault_state", level.value)
        Pub().pub("openWB/set/optional/forecast/get/fault_str", message)

    def _is_update_due(self) -> bool:
        """Prüfe, ob eine Prognose-Aktualisierung fällig ist.
        
        Gibt False sofort zurück, wenn die Konfiguration unvollständig ist (verhindert API-Aufrufe vor dem Speichern).
        Prüft sonst, ob die geplante Aktualisierungszeit erreicht wurde.
        """
        if not self._is_config_complete():
            return False
        
        return self.get.next_query_time is None or self.get.next_query_time == 0 or self.get.next_query_time <= timecheck.create_timestamp()

    def _is_force_update_requested(self) -> bool:
        return bool(self.get.force_update)

    def _clear_force_update_request(self) -> None:
        if self.get.force_update:
            self.get.force_update = False
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

    def _get_forecast_data(self):
        """Rufe Referenz zu den globalen Prognosedaten aus SubData ab."""
        from helpermodules import subdata
        return subdata.SubData.optional_data.data.forecast

    def update(self) -> None:
        force_update = self._is_force_update_requested()
        if not force_update and not self._is_update_due():
            return
        try:
            trigger_mode = "manuell" if force_update else "geplant"
            log.info("Prognose-Aktualisierung gestartet (Anbieter=%s, Auslöser=%s)", self.config.type, trigger_mode)
            state = self._component_updater()
            self.store.set(state)
            self.store.update()
            self._set_next_query_time_by_schedule()
            self._publish_forecast_fault(FaultStateLevel.NO_ERROR, NO_ERROR)
            forecast_data = self._get_forecast_data()
            forecast_data.configured = True
            forecast_data.provider = asdict(self.config)
            now_ts = int(datetime.now().timestamp())
            self.get.last_update_time = now_ts
            Pub().pub("openWB/set/optional/forecast/get/last_update_time", now_ts)
            log.info(
                "Prognose-Aktualisierung beendet (Anbieter=%s, Werte=%s, nächste_Aktualisierungszeit=%s)",
                self.config.type,
                len(state.forecast_values or {}),
                self.get.next_query_time,
            )
        except Exception as e:
            error_str = str(e)
            if "429" in error_str:
                # Rate-limitierte Anbieter sollten bis zum nächsten geplanten Update-Zeitfenster warten.
                self._set_next_query_time_by_schedule()
                self._publish_forecast_fault(
                    FaultStateLevel.WARNING,
                    "Forecast-API-Ratenlimit erreicht (HTTP 429). Warte auf nächste geplante Aktualisierung.",
                )
            elif "Missing required" in error_str or "required forecast config field" in error_str.lower():
                # Konfiguration ist unvollständig; keine automatische Wiederholung.
                # Nächster Versuch beim nächsten geplanten Zeitpunkt oder manuellem Auslöser.
                self._set_next_query_time_by_schedule()
                self._publish_forecast_fault(
                    FaultStateLevel.WARNING,
                    f"Prognose-Konfiguration unvollständig: {error_str}. Bitte alle erforderlichen Felder konfigurieren.",
                )
            else:
                self._set_retry_query_time()
                self._publish_forecast_fault(
                    FaultStateLevel.WARNING,
                    "Prognose-Aktualisierung fehlgeschlagen. Wiederholung in 15 Minuten geplant.",
                )
            log.exception(f"Fehler beim Aktualisieren der Prognosedaten: {e}")
        finally:
            self._clear_force_update_request()


class ConfigurableForecastProvider(ConfigurableForecast[T_FORECAST_CONFIG]):
    def __init__(self,
                 config: T_FORECAST_CONFIG,
                 component_initializer: Callable[[T_FORECAST_CONFIG], ForecastState]) -> None:
        super().__init__(config, component_initializer)
