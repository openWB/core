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
TARIFF_UPDATE_HOUR = 14  # latest expected time for daily tariff update
ONE_HOUR_SECONDS: int = 3600
log = logging.getLogger(__name__)
'''
next_query_time and internal_tariff_state are defined outside of class ConfigurableElectricityTariff because
for an unknown reason defining them as a class variable does not keep their values.
'''
next_query_time: datetime = datetime.fromtimestamp(1)
internal_tariff_state: TariffState = None


class ConfigurableElectricityTariff(Generic[T_TARIFF_CONFIG]):
    def __init__(self,
                 config: T_TARIFF_CONFIG,
                 component_initializer: Callable[[], float]) -> None:
        global internal_tariff_state, next_query_time
        next_query_time = datetime.now()
        internal_tariff_state = None
        self.config = config
        self.store = store.get_electricity_tariff_value_store()
        self.fault_state = FaultState(ComponentInfo(None, self.config.name, ComponentType.ELECTRICITY_TARIFF.value))
        # nach Init auf NO_ERROR setzen, damit der Fehlerstatus beim Modulwechsel gelöscht wird
        self.fault_state.no_error()
        self.fault_state.store_error()
        with SingleComponentUpdateContext(self.fault_state):
            self._component_updater = component_initializer(config)

    def update(self) -> None:
        if hasattr(self, "_component_updater"):
            with SingleComponentUpdateContext(self.fault_state):
                tariff_state, timeslot_length_seconds = self.__update_et_provider_data(internal_tariff_state)
                self.__store_and_publish_updated_data(tariff_state)
                self.__log_and_publish_progress(timeslot_length_seconds)

    def __update_et_provider_data(self, tariff_state: TariffState) -> tuple[TariffState, int]:
        tariff_state = self.__query_et_provider_data_once_per_day(internal_tariff_state)
        timeslot_length_seconds = self.__calculate_price_timeslot_length(tariff_state)
        tariff_state = self._remove_outdated_prices(tariff_state, timeslot_length_seconds)
        return tariff_state, timeslot_length_seconds

    def __query_et_provider_data_once_per_day(self, tariff_state: TariffState) -> TariffState:
        if datetime.now() > next_query_time:
            return self.__query_et_provider_data(tariff_state=tariff_state)
        else:
            return tariff_state

    def __query_et_provider_data(self, tariff_state: TariffState) -> TariffState:
        def is_tomorrow(last_timestamp: str) -> bool:
            return (self.__day_of(date=datetime.now()) < self.__day_of(datetime.fromtimestamp(int(last_timestamp)))
                    or self.__day_of(date=datetime.now()).hour < TARIFF_UPDATE_HOUR)
        global next_query_time
        log.info(f'Wartezeit {next_query_time.strftime("%Y%m%d-%H:%M:%S")}'
                 ' abgelaufen, Strompreise werden abgefragt'
                 )
        try:
            new_tariff_state = self._component_updater()
            if 0 < len(new_tariff_state.prices):
                if is_tomorrow(self.__get_last_entry_time_stamp(new_tariff_state)):
                    next_query_time = self.__calulate_next_query_time(new_tariff_state)
                    log.info('Nächster Abruf der Strompreise'
                             f' {next_query_time.strftime("%Y%m%d-%H:%M:%S")}.')
                else:
                    log.info('Keine Daten für morgen erhalten, weiterer Versuch in 5 Minuten')
                return new_tariff_state
            else:
                log.warning('Leere Preisliste erhalten, weiterer Versuch in 5 Minuten.')
                return tariff_state
        except Exception as e:
            log.warning(f'Fehler beim Abruf der Strompreise: {e}, nächster Versuch in 5 Minuten.')
            self.fault_state.warning(
                f'Fehler beim Abruf der Strompreise: {e}, nächster Versuch in 5 Minuten.')
            return tariff_state

    def __day_of(self, date: datetime) -> datetime:
        return date.replace(hour=0, minute=0, second=0, microsecond=0)

    def __next_query_message(self) -> str:
        tomorrow = (
            ''
            if self.__day_of(datetime.now()) == self.__day_of(next_query_time)
            else 'morgen '
        )
        return (
            f'{tomorrow}{next_query_time.strftime("%H:%M")}'
            if datetime.now() < next_query_time
            else "im nächsten Regelzyklus"
        )

    def __log_and_publish_progress(self, timeslot_length_seconds):
        def publish_info(message_extension: str) -> None:
            self.fault_state.no_error(
                f'Die Preisliste hat {message_extension}{len(internal_tariff_state.prices)} Einträge. '
                f'Nächster Abruf der Strompreise {self.__next_query_message()}.')
        expected_time_slots = int(24 * ONE_HOUR_SECONDS / timeslot_length_seconds)
        publish_info(f'nicht {expected_time_slots}, sondern '
                     if len(internal_tariff_state.prices) < expected_time_slots
                     else ''
                     )

    def __store_and_publish_updated_data(self, tariff_state: TariffState) -> None:
        global internal_tariff_state
        internal_tariff_state = tariff_state
        self.store.set(tariff_state)
        self.store.update()

    def __calulate_next_query_time(self, tariff_state: TariffState) -> datetime:
        return datetime.fromtimestamp(int(max(tariff_state.prices))).replace(
            hour=TARIFF_UPDATE_HOUR, minute=0, second=0
        ) + timedelta(
            # aktually ET providers issue next day prices up to half an hour earlier then 14:00
            # reduce serverload on their site by trying early and randomizing query time
            minutes=random.randint(1, 7) * -5
        )

    def __calculate_price_timeslot_length(self, tariff_state: TariffState) -> int:
        if (tariff_state is None or
                tariff_state.prices is None or
                len(tariff_state.prices) < 2):
            self.fault_state.error("not enough price entries to calculate timeslot length")
            return 1
        else:
            first_timestamps = list(tariff_state.prices.keys())[:2]
            return int(first_timestamps[1]) - int(first_timestamps[0])

    def __get_last_entry_time_stamp(self, tariff_state: TariffState) -> str:
        last_known_timestamp = "0"
        if tariff_state is not None:
            last_known_timestamp = max(tariff_state.prices)
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
