from typing import TypeVar, Generic, Callable
from datetime import datetime, timedelta
from helpermodules import timecheck
import random
import logging
from modules.common import store
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import TariffState
from modules.common.component_type import ComponentType
from modules.common.fault_state import ComponentInfo, FaultState


T_TARIFF_CONFIG = TypeVar("T_TARIFF_CONFIG")
ONE_HOUR_SECONDS: int = 3600
log = logging.getLogger(__name__)


class ConfigurableElectricityTariff(Generic[T_TARIFF_CONFIG]):
    def __init__(self,
                 config: T_TARIFF_CONFIG,
                 component_initializer: Callable[[], float]) -> None:
        self.__next_query_time = datetime.fromtimestamp(1)
        self.__tariff_state: TariffState = None
        self.config = config
        self.store = store.get_electricity_tariff_value_store()
        self.fault_state = FaultState(ComponentInfo(None, self.config.name, ComponentType.ELECTRICITY_TARIFF.value))
        # nach Init auf NO_ERROR setzen, damit der Fehlerstatus beim Modulwechsel gelöscht wird
        self.fault_state.no_error()
        self.fault_state.store_error()
        with SingleComponentUpdateContext(self.fault_state):
            self._component_updater = component_initializer(config)

    def update(self):
        if hasattr(self, "_component_updater"):
            with SingleComponentUpdateContext(self.fault_state):
                self.__query_et_provider_data_once_per_day()
                timeslot_length_seconds = self.__calculate_price_timeslot_length()
                self.__tariff_state = self._remove_outdated_prices(self.__tariff_state, timeslot_length_seconds)
                self.__store_and_publish_updated_data()
                self.__log_and_publish_progress(timeslot_length_seconds)

    def __query_et_provider_data_once_per_day(self):
        def is_tomorrow(last_timestamp: str) -> bool:
            return self.__day_of(date=datetime.now()) < self.__day_of(datetime.fromtimestamp(int(last_timestamp)))
        if datetime.now() > self.__next_query_time:
            log.info(f'Wartezeit {self.__next_query_time.strftime("%Y%m%d-%H:%M:%S")}'
                     ' abgelaufen, Strompreise werden abgefragt')
            try:
                new_tariff_state = self._component_updater()
                if (0 < len(new_tariff_state.prices) and is_tomorrow(max(new_tariff_state.prices))):
                    self.__tariff_state = new_tariff_state
                    self.__calulate_next_query_time()
                else:
                    log.info('Keine Daten für morgen erhalten, weiterer Versuch in 5 Minuten')
            except Exception as e:
                log.warning(f'Fehler beim Abruf der Strompreise: {e}, nächster Versuch in 5 Minuten.')
                self.fault_state.warning(
                    f'Fehler beim Abruf der Strompreise: {e}, nächster Versuch in 5 Minuten.'
                )
            log.info(f'Nächster Abruf der Strompreise frühestens {self.__next_query_time.strftime("%Y%m%d-%H:%M:%S")}.')

    def __day_of(self, date: datetime) -> datetime:
        return date.replace(hour=0, minute=0, second=0, microsecond=0)

    def __next_query_message(self) -> str:
        tomorrow = (
            ''
            if self.__day_of(datetime.now()) == self.__day_of(self.__next_query_time)
            else 'morgen '
        )
        return (
            f'frühestens {tomorrow}{self.__next_query_time.strftime("%H:%M")}'
            if datetime.now() < self.__next_query_time
            else "im nächsten Regelzyklus"
        )

    def __log_and_publish_progress(self, timeslot_length_seconds):
        def publish_info(message_extension: str) -> None:
            self.fault_state.no_error(
                f'Die Preisliste hat {message_extension}{len(self.__tariff_state.prices)} Einträge. '
                f'Nächster Abruf der Strompreise {self.__next_query_message()}.')
        expected_time_slots = int(24 * ONE_HOUR_SECONDS / timeslot_length_seconds)
        publish_info(f'nicht {expected_time_slots}, sondern '
                     if len(self.__tariff_state.prices) < expected_time_slots
                     else ''
                     )

    def __store_and_publish_updated_data(self):
        self.store.set(self.__tariff_state)
        self.store.update()

    def __calulate_next_query_time(self) -> None:
        self.__next_query_time = datetime.now().replace(
            hour=14, minute=0, second=0
        ) + timedelta(
            # aktually ET providers issue next day prices up to half an hour earlier then 14:00
            # reduce serverload on their site by trying early and randomizing query time
            minutes=random.randint(-30, -10),
            seconds=random.randint(0, 59)
        )
        if datetime.now() > self.__next_query_time:
            self.__next_query_time += timedelta(days=1)

    def __calculate_price_timeslot_length(self) -> int:
        first_timestamps = list(self.__tariff_state.prices.keys())[:2]
        return int(first_timestamps[1]) - int(first_timestamps[0])

    def __get_last_entry_time_stamp(self) -> str:
        last_known_timestamp = "0"
        if self.__tariff_state is not None:
            last_known_timestamp = max(self.__tariff_state.prices)
        return last_known_timestamp

    def _remove_outdated_prices(self, tariff_state: TariffState, timeslot_length_seconds: int) -> TariffState:
        if tariff_state.prices is None:
            self.fault_state.error("no prices to show")
        else:
            now = timecheck.create_timestamp()
            for timestamp in list(tariff_state.prices.keys()):
                if int(timestamp) < now - (timeslot_length_seconds - 1):  # keep current time slot
                    tariff_state.prices.pop(timestamp)
                    log.debug(
                        'Die Preisliste startet nicht mit der aktuellen Stunde. '
                        f'Eintrag {timestamp} wurden entfernt. rest: {tariff_state.prices}')
        return tariff_state
