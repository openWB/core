from datetime import datetime, timedelta
import random
from typing import Dict, TypeVar, Generic, Callable
import requests
from helpermodules import timecheck
import logging
from helpermodules.pub import Pub
from modules.common import store
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import TariffState
from modules.common.component_type import ComponentType
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.tariff_errors import PermanentTariffError
from control.optional_data import OptionalData, PricingGet


# Stunden für tägliche Tarifaktualisierung, manche Anbieter aktualisieren mehrfach täglich
T_TARIFF_CONFIG = TypeVar("T_TARIFF_CONFIG")
ONE_HOUR_SECONDS: int = 3600
# Die Preise für den Folgetag werden meist ab ca. 14 Uhr veröffentlicht (Anbieter mit anderer Zeit setzen
# first_try_hour in ihrer Tarifklasse). Erster Abruf 5-30 Minuten vorher (zufällig, um die Last der Anbieter zu
# verteilen), danach stündlich, bis sie da sind.
FIRST_TRY_HOUR: int = 14
RETRY_INTERVAL_SECONDS: int = ONE_HOUR_SECONDS
# So viele Stunden nach dem ersten Abruf wird ein fehlender Folgetag gewarnt, der Abruf läuft stündlich weiter
TOMORROW_WARNING_DELAY_HOURS: int = 5
# Wartezeit nach einer Exception oder wenn kein Preis den aktuellen Zeitpunkt abdeckt (siehe #3703)
RETRY_BACKOFF_SECONDS: int = 5 * 60
# Nach einem dauerhaften Fehler (z.B. falsche Zugangsdaten) wird erst nach einer Änderung der Konfiguration
# wieder abgefragt
PERMANENT_ERROR_PARK_SECONDS: int = 365 * 24 * ONE_HOUR_SECONDS

log = logging.getLogger(__name__)


class ConfigurableTariff(Generic[T_TARIFF_CONFIG]):
    def __init__(self,
                 config: T_TARIFF_CONFIG,
                 component_initializer: Callable[[], float],
                 get: PricingGet,
                 tariff_type: str = "flexible_tariff") -> None:
        self.config = config
        self.get = get
        self.tariff_type = tariff_type

        # Anbieter, die erst um 0 Uhr die Preise des laufenden Tages liefern, haben keine Folgetagspreise
        self.publishes_day_ahead = getattr(config, "publishes_day_ahead", True)
        self.first_try_hour = getattr(config, "first_try_hour", FIRST_TRY_HOUR)

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
                    if self._is_permanent_error(e):
                        self.fault_state.error(f"{self.fault_state.fault_str} - Es wird erst nach einer Änderung der "
                                               "Konfiguration erneut abgefragt.")
                        self.fault_state.store_error()
                        self._set_next_query_time(int(timecheck.create_timestamp()) + PERMANENT_ERROR_PARK_SECONDS)
                    else:
                        self._delay_next_query()
            else:
                log.info(f"nächste Tarifaktualisierung für {self.tariff_type}" +
                         f" um {datetime.fromtimestamp(self.get.next_query_time)}")

    def __update_et_provider_data(self) -> tuple[TariffState, int]:
        tariff_state = self.__call_component_updater()
        timeslot_length_seconds = self.__calculate_price_timeslot_length(tariff_state)
        tariff_state = self._remove_outdated_prices(tariff_state, timeslot_length_seconds)
        return tariff_state, timeslot_length_seconds

    @staticmethod
    def _is_permanent_error(exception: Exception) -> bool:
        if isinstance(exception, PermanentTariffError):
            return True
        return (isinstance(exception, requests.HTTPError) and exception.response is not None and
                exception.response.status_code in (401, 403))

    def _first_try(self, day: datetime) -> datetime:
        return day.replace(hour=self.first_try_hour, minute=0, second=0, microsecond=0) - timedelta(
            minutes=random.randint(1, 6) * 5)

    def _schedule_next_query(self, prices: Dict[str, float], timeslot_length_seconds: int) -> None:
        now = datetime.now()
        if not prices:
            self._delay_next_query()
            return
        latest_start = datetime.fromtimestamp(max(int(ts) for ts in prices))
        prices_end = latest_start + timedelta(seconds=timeslot_length_seconds)
        if prices_end <= now:
            # Kein Preis für den aktuellen Zeitpunkt: bei Anbietern, die um 0 Uhr die Preise des Tages liefern, ist das
            # kurz nach Mitternacht normal, sonst eine Störung des Anbieters, die nicht minütlich abgefragt werden muss
            self._delay_next_query(RETRY_BACKOFF_SECONDS if not self.publishes_day_ahead else RETRY_INTERVAL_SECONDS)
            return
        if not self.publishes_day_ahead:
            next_query = prices_end
        else:
            tomorrow = now + timedelta(days=1)
            tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
            if latest_start >= tomorrow_start:
                next_query = self._first_try(tomorrow)
            else:
                # Folgetag fehlt: bis zum ersten Abruf des Tages warten, danach stündlich wiederholen. Nach Mitternacht
                # endet damit die Wiederholung (siehe #3703: rollierende Antworten erreichen den Folgetag nie).
                first_try = self._first_try(now)
                next_query = first_try if now < first_try else now + timedelta(seconds=RETRY_INTERVAL_SECONDS)
        # spätestens, wenn die bekannten Preise ablaufen
        next_query = min(next_query, prices_end)
        self._set_next_query_time(int(next_query.timestamp()))
        log.debug(f"Nächster Abruf der {self.tariff_type} Strompreise geplant für: {next_query}")

    def __call_component_updater(self) -> TariffState:
        last_known_timestamp = max((int(ts) for ts in self.get.prices.keys()), default=0)
        tariff_state = self._component_updater()
        latest_price_timestamp = max((int(ts) for ts in tariff_state.prices.keys()), default=0)
        if latest_price_timestamp <= last_known_timestamp:
            # Keine neueren Preise, z.B. weil die Preise für den Folgetag noch nicht veröffentlicht sind: die
            # bekannten Preise behalten (siehe #3703)
            tariff_state = TariffState(prices=dict(self.get.prices))
        self._schedule_next_query(tariff_state.prices, self.__calculate_price_timeslot_length(tariff_state))
        return tariff_state

    def _delay_next_query(self, seconds: int = RETRY_BACKOFF_SECONDS) -> None:
        self._set_next_query_time(int(timecheck.create_timestamp()) + seconds)

    def _set_next_query_time(self, next_query_time: int) -> None:
        self.get.next_query_time = next_query_time
        Pub().pub(f"openWB/set/optional/ep/{self.tariff_type}/get/next_query_time", next_query_time)

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
        if not self.publishes_day_ahead or now.hour < self.first_try_hour + TOMORROW_WARNING_DELAY_HOURS:
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
