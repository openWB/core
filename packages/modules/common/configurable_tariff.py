from datetime import datetime, timedelta
import math
import random
from typing import TypeVar, Generic, Callable
from helpermodules import timecheck
import logging
from helpermodules.pub import Pub
from modules.common import store
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import TariffState
from modules.common.component_type import ComponentType
from modules.common.fault_state import ComponentInfo, FaultState
from control.optional_data import OptionalData, PricingGet


# Stunden für tägliche Tarifaktualisierung, manche Anbieter aktualisieren mehrfach täglich
T_TARIFF_CONFIG = TypeVar("T_TARIFF_CONFIG")
ONE_HOUR_SECONDS: int = 3600
# Wartezeit vor dem nächsten Versuch nach einem Abruf ohne neue Preise oder einer Exception (siehe #3703)
RETRY_BACKOFF_SECONDS: int = 5 * 60
# So viele Stunden nach der ersten konfigurierten Tarifaktualisierungsstunde löst ein immer noch
# fehlender Preis für den Folgetag eine Warnung aus statt stillschweigend weiter zu versuchen -
# vorher ist das noch der normale, erwartete Fall
LATE_WARNING_OFFSET_HOURS: int = 2

log = logging.getLogger(__name__)


class ConfigurableTariff(Generic[T_TARIFF_CONFIG]):
    # Default value, may be overridden in __init__ if config provides it
    tariff_update_hours = [14]

    def __init__(self,
                 config: T_TARIFF_CONFIG,
                 component_initializer: Callable[[], float],
                 get: PricingGet,
                 tariff_type: str = "flexible_tariff") -> None:
        self.config = config
        self.get = get
        self.tariff_type = tariff_type

        # Set update_hours from config if available, else default to [14]
        if hasattr(config.configuration, 'update_hours') and config.configuration.update_hours is not None:
            self.tariff_update_hours = config.configuration.update_hours

        # nach Init auf NO_ERROR setzen, damit der Fehlerstatus beim Modulwechsel gelöscht wird
        self.fault_state.no_error()
        self.fault_state.store_error()
        try:
            self._component_updater = component_initializer(config)
        except Exception as e:
            # nicht reraisen, sonst bliebe bei subdata.py's Zuweisung das alte Modul aktiv
            log.exception(f"Fehler beim Initialisieren von {tariff_type}: {e}")
            self.fault_state.from_exception(e)
            self.fault_state.store_error()

    def update(self) -> None:
        if hasattr(self, "_component_updater"):
            if self.get.next_query_time is None or self.get.next_query_time <= timecheck.create_timestamp():
                log.debug(f"Tarifaktualisierung für {self.tariff_type}")
                try:
                    # reraise=True, sonst verschluckt __exit__ die Exception vor dem except-Block (siehe #3703)
                    with SingleComponentUpdateContext(self.fault_state, reraise=True):
                        tariff_state, timeslot_length_seconds = self.__update_et_provider_data()
                        self.__store_and_publish_updated_data(tariff_state)
                        self.__finalize_update_status(timeslot_length_seconds, tariff_state)
                except Exception as e:
                    log.exception(f"Fehler beim Aktualisieren der Tarifdaten {e}")
                    self._delay_next_query()
            else:
                log.info(f"nächste Tarifaktualisierung für {self.tariff_type}" +
                         f" um {datetime.fromtimestamp(self.get.next_query_time)}")

    def __update_et_provider_data(self) -> tuple[TariffState, int]:
        tariff_state = self.__call_component_updater()
        timeslot_length_seconds = self.__calculate_price_timeslot_length(tariff_state)
        tariff_state = self._remove_outdated_prices(tariff_state, timeslot_length_seconds)
        return tariff_state, timeslot_length_seconds

    def _calculate_next_query_time(self, latest_price_timestamp: datetime) -> None:
        now = datetime.now()
        current_hour = now.hour + 1  # next full hour
        log.debug(f"Aktuelle Tarif Update Stunde: {current_hour} Uhr."
                  f" Berechne nächsten Abruf der {self.tariff_type} Strompreise.")
        log.debug(f"Konfigurierte Tarifaktualisierungsstunden für {self.tariff_type} : {self.tariff_update_hours}")
        next_hour = min([hour for hour in self.tariff_update_hours
                         if hour > current_hour], default=self.tariff_update_hours[0])
        log.debug(f"Nächste Tarifaktualisierungsstunde: {next_hour} Uhr.")
        day_offset = 0 if next_hour > current_hour else 1
        log.debug(f"Berechneter Tagsoffset für nächsten Abruf: {day_offset} Tage.")

        # reduce serverload on their site by trying early and randomizing query time minutes and seconds
        next_query_time = (now.replace(hour=next_hour, minute=0, second=0, microsecond=0) +
                           timedelta(days=day_offset, minutes=random.randint(1, 7) * -5))
        if latest_price_timestamp < next_query_time:
            tomorrow_start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            warning_hour = min(self.tariff_update_hours) + LATE_WARNING_OFFSET_HOURS
            if latest_price_timestamp < tomorrow_start and now.hour < warning_hour:
                # Noch keine Preise für den Folgetag und die Warnschwelle ist noch nicht erreicht:
                # kurzer Backoff statt auf das Ende der heute schon bekannten Preise zu springen.
                # Sonst würde bei Anbietern mit rollierender Tagesantwort (Preise reichen jeden
                # Abruf etwas weiter in den noch laufenden Tag, ohne je den Folgetag zu erreichen)
                # der Abruf für Stunden pausiert, noch bevor überhaupt die Warnschwelle erreicht ist
                # (siehe #3703).
                self._delay_next_query()
                return
            # Falls die Preise nicht bis zum nächsten geplanten Abruf gültig sind,
            # den Abruf auf die Gültigkeitsdauer der Preise setzen
            log.debug(f"Die Preise sind nur bis {latest_price_timestamp} gültig, "
                      f"setze nächsten Abruf auf dieses Datum.")
            next_query_time = latest_price_timestamp
        if next_query_time <= now:
            # Zeit um so viele volle Stunden erhöhen, bis sie in der Zukunft liegt, Minute-Offset bleibt erhalten
            delta_seconds = (now - next_query_time).total_seconds()
            hours_to_add = max(1, math.floor(delta_seconds / ONE_HOUR_SECONDS) + 1)
            next_query_time = next_query_time + timedelta(hours=hours_to_add)
        self.get.next_query_time = int(next_query_time.timestamp())
        log.debug(f"Nächster Abruf der {self.tariff_type} Strompreise geplant für:"
                  f" {next_query_time} (Unix Timestamp: {self.get.next_query_time})")
        Pub().pub(f"openWB/set/optional/ep/{self.tariff_type}/get/next_query_time", int(next_query_time.timestamp()))

    def __call_component_updater(self) -> TariffState:
        last_known_timestamp = datetime.fromtimestamp(max((int(ts) for ts in self.get.prices.keys()), default=0))
        tariff_state = self._component_updater()
        latest_price_timestamp = datetime.fromtimestamp(max((int(ts) for ts in tariff_state.prices.keys()), default=0))
        if last_known_timestamp < latest_price_timestamp:
            self._calculate_next_query_time(latest_price_timestamp)
        else:
            # Anbieter hat (noch) keine neueren Preise geliefert, z.B. weil die Preise für den
            # Folgetag noch nicht veröffentlicht sind - ohne Backoff würde sonst jeden Regelzyklus
            # neu abgefragt, bis es welche gibt (siehe #3703)
            self._delay_next_query()
        return tariff_state

    def _delay_next_query(self) -> None:
        self.get.next_query_time = int(timecheck.create_timestamp()) + RETRY_BACKOFF_SECONDS
        Pub().pub(f"openWB/set/optional/ep/{self.tariff_type}/get/next_query_time", self.get.next_query_time)

    def __finalize_update_status(self, timeslot_length_seconds: int, tariff_state: TariffState) -> None:
        # einziger Ort, der den fault_state setzt - sonst überschreibt ein abschließendes no_error()
        # jede zuvor gesetzte Warnung/Fehler sofort wieder (siehe #3703)
        if tariff_state.prices is None or len(tariff_state.prices) < 2:
            self.fault_state.error(
                f"Nicht genug Preiseinträge für {self.tariff_type}, um die Zeitschrittlänge zu berechnen.")
            return
        if self.__is_tomorrow_price_missing_after_late_hour(tariff_state):
            self.fault_state.warning(
                f"Noch keine aktuellen Preise für {self.tariff_type} erhalten - "
                "der Anbieter liefert bisher keine Daten für den Folgetag.")
            return
        expected_time_slots = int(24 * ONE_HOUR_SECONDS / timeslot_length_seconds)
        message_extension = (f'nicht {expected_time_slots}, sondern ' if len(tariff_state.prices) < expected_time_slots
                             else '')
        self.fault_state.no_error(
            f'Die {self.tariff_type} Preisliste hat {message_extension}{len(tariff_state.prices)} Einträge. ')

    def __is_tomorrow_price_missing_after_late_hour(self, tariff_state: TariffState) -> bool:
        now = datetime.now()
        warning_hour = min(self.tariff_update_hours) + LATE_WARNING_OFFSET_HOURS
        if now.hour < warning_hour:
            return False
        # Datum vor dem Nullsetzen der Uhrzeit erhöhen - +24h in Sekunden träfe an Tagen mit Zeitumstellung
        # nicht auf Mitternacht
        tomorrow_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = int(tomorrow_midnight.timestamp())
        return max(int(ts) for ts in tariff_state.prices.keys()) < tomorrow_start

    def __store_and_publish_updated_data(self, tariff_state: TariffState) -> None:
        self.store.set(tariff_state)
        self.store.update()

    def __calculate_price_timeslot_length(self, tariff_state: TariffState) -> int:
        # <2 Einträge werden in __finalize_update_status() gemeldet, hier nur Platzhalter gegen Division durch 0
        if (tariff_state is None or
                tariff_state.prices is None or
                len(tariff_state.prices) < 2):
            return 1
        else:
            first_timestamps = list(tariff_state.prices.keys())[:2]
            return int(first_timestamps[1]) - int(first_timestamps[0])

    def _remove_outdated_prices(self, tariff_state: TariffState, timeslot_length_seconds: int) -> TariffState:
        # prices is None wird in __finalize_update_status() gemeldet
        if tariff_state.prices is not None:
            now = timecheck.create_timestamp()
            first_timestamp = int(max([int(timestamp) for timestamp in tariff_state.prices.keys()
                                      if int(timestamp) <= now], default=0))
            tariff_state.prices = {str(timestamp): price for timestamp, price in tariff_state.prices.items()
                                   if int(timestamp) >= first_timestamp}
        return tariff_state


class ConfigurableFlexibleTariff(ConfigurableTariff):
    def __init__(self,
                 config: T_TARIFF_CONFIG,
                 component_initializer: Callable[[], float]) -> None:
        self.store = store.get_flexible_tariff_value_store()
        self.fault_state = FaultState(ComponentInfo(None, config.name, ComponentType.FLEXIBLE_TARIFF.value))
        super().__init__(config, component_initializer, OptionalData().electricity_pricing.flexible_tariff.get)


class ConfigurableGridFee(ConfigurableTariff):
    def __init__(self,
                 config: T_TARIFF_CONFIG,
                 component_initializer: Callable[[], float]) -> None:
        self.store = store.get_grid_fee_value_store()
        self.fault_state = FaultState(ComponentInfo(None, config.name, ComponentType.GRID_FEE.value))
        super().__init__(config, component_initializer, OptionalData().electricity_pricing.grid_fee.get,
                         tariff_type="grid_fee")
