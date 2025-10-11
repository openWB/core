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

    def __calulate_next_query_time(self) -> None:
        self.__next_query_time = datetime.now().replace(
            hour=14, minute=0, second=0
        ) + timedelta(
            # aktually ET providers issue next day prices up to half an hour earlier then 14:00
            # reduce serverload on their site by randomizing query time
            minutes=random.randint(-7, 7),
            seconds=random.randint(0, 59)
        )
        if datetime.now() > self.__next_query_time:
            self.__next_query_time += timedelta(days=1)

    def update(self):
        if hasattr(self, "_component_updater"):
            if datetime.now() > self.__next_query_time:
                # Wenn beim Initialisieren etwas schief gelaufen ist, ursprüngliche Fehlermeldung beibehalten
                with SingleComponentUpdateContext(self.fault_state):
                    self.__tariff_state = self._component_updater()
                    self.__calulate_next_query_time()
            log.debug(f'nächster Abruf der Strompreise nach {self.__next_query_time.strftime("%Y%m%d-%H:%M")}')
            timeslot_length_seconds = self.__calculate_price_timeslot_length()
            self.__tariff_state = self._remove_outdated_prices(self.__tariff_state, timeslot_length_seconds)
            self.store.set(self.__tariff_state)
            self.store.update()
            expected_time_slots = int(24 * ONE_HOUR_SECONDS / timeslot_length_seconds)
            if len(self.__tariff_state.prices) < expected_time_slots:
                self.fault_state.no_error(
                    f'Die Preisliste hat nicht {expected_time_slots}, '
                    f'sondern {len(self.__tariff_state.prices)} Einträge. '
                    f'nächster Abruf der Strompreise nach {self.__next_query_time.strftime("%Y%m%d-%H:%M")}')

    def __calculate_price_timeslot_length(self) -> int:
        first_timestamps = list(self.__tariff_state.prices.keys())[:2]
        return int(first_timestamps[1]) - int(first_timestamps[0])

    def _remove_outdated_prices(self, tariff_state: TariffState, timeslot_length_seconds: int) -> TariffState:
        now = timecheck.create_timestamp()
        for timestamp in list(tariff_state.prices.keys()):
            if int(timestamp) < now - (timeslot_length_seconds - 1):  # keep current time slot
                self.fault_state.warning(
                    'Die Preisliste startet nicht mit der aktuellen Stunde. '
                    'Abgelaufene Einträge wurden entfernt.')
                tariff_state.prices.pop(timestamp)
        self.fault_state.no_error(
            f'Die Preisliste hat {len(tariff_state.prices)} Einträge. ')
        return tariff_state
