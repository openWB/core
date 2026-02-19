from datetime import datetime, timedelta
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


# Stunden für tägliche Tarifaktualisierung, manche Anbieter aktualisieren mehrfach täglich
TARIFF_UPDATE_HOURS = [2, 8, 14, 20]
T_TARIFF_CONFIG = TypeVar("T_TARIFF_CONFIG")
TARIFF_UPDATE_HOUR = 14  # latest expected time for daily tariff update
ONE_HOUR_SECONDS: int = 3600

log = logging.getLogger(__name__)


class ConfigurableTariff(Generic[T_TARIFF_CONFIG]):
    def __init__(self,
                 config: T_TARIFF_CONFIG,
                 component_initializer: Callable[[], float]) -> None:
        self.config = config

        # nach Init auf NO_ERROR setzen, damit der Fehlerstatus beim Modulwechsel gelöscht wird
        self.fault_state.no_error()
        self.fault_state.store_error()
        with SingleComponentUpdateContext(self.fault_state):
            self._component_updater = component_initializer(config)

    def update(self) -> None:
        if hasattr(self, "_component_updater"):
            try:
                with SingleComponentUpdateContext(self.fault_state):
                    tariff_state, timeslot_length_seconds = self.__update_et_provider_data()
                    self.__store_and_publish_updated_data(tariff_state)
                    self.__log_and_publish_progress(timeslot_length_seconds, tariff_state)
            except Exception as e:
                log.exception(f"Fehler beim Aktualisieren der Tarifdaten {e}")
                self.fault_state.warning("Error updating tariff data, retry in 5 minutes")

    def __update_et_provider_data(self) -> tuple[TariffState, int]:
        tariff_state = self.__call_component_updater()
        timeslot_length_seconds = self.__calculate_price_timeslot_length(tariff_state)
        tariff_state = self._remove_outdated_prices(tariff_state, timeslot_length_seconds)
        return tariff_state, timeslot_length_seconds

    def __calculate_next_query_time(self) -> float:
        now = datetime.now()
        current_hour = now.hour
        next_hour = min([hour for hour in TARIFF_UPDATE_HOURS
                         if hour > current_hour], default=TARIFF_UPDATE_HOURS[0])
        # reduce serverload on their site by trying early and randomizing query time minutes and seconds
        next_query_time = (now.replace(hour=next_hour, minute=0, second=0, microsecond=0) +
                           timedelta(days=1, minutes=random.randint(1, 7) * -5))
        Pub().pub("openWB/set/optional/ep/get/next_query_time", int(next_query_time.timestamp()))

    def __call_component_updater(self) -> TariffState:
        tariff_state = self._component_updater()
        self.__calculate_next_query_time()
        return tariff_state

    def __log_and_publish_progress(self, timeslot_length_seconds, tariff_state):
        def publish_info(message_extension: str) -> None:
            self.fault_state.no_error(
                f'Die Preisliste hat {message_extension}{len(tariff_state.prices)} Einträge. ')
        expected_time_slots = int(24 * ONE_HOUR_SECONDS / timeslot_length_seconds)
        publish_info(f'nicht {expected_time_slots}, sondern '
                     if len(tariff_state.prices) < expected_time_slots
                     else ''
                     )

    def __store_and_publish_updated_data(self, tariff_state: TariffState) -> None:
        self.store.set(tariff_state)
        self.store.update()

    def __calculate_price_timeslot_length(self, tariff_state: TariffState) -> int:
        if (tariff_state is None or
                tariff_state.prices is None or
                len(tariff_state.prices) < 2):
            self.fault_state.error("not enough price entries to calculate timeslot length")
            return 1
        else:
            first_timestamps = list(tariff_state.prices.keys())[:2]
            return int(first_timestamps[1]) - int(first_timestamps[0])

    def _remove_outdated_prices(self, tariff_state: TariffState, timeslot_length_seconds: int) -> TariffState:
        if tariff_state.prices is None:
            self.fault_state.error("no prices to show")
        else:
            now = timecheck.create_timestamp()
            removed = False
            for timestamp in list(tariff_state.prices.keys()):
                if int(timestamp) < now - (timeslot_length_seconds - 1):  # keep current time slot
                    tariff_state.prices.pop(timestamp)
                    removed = True
            if removed:
                log.debug(
                    'Die Preisliste startet nicht mit der aktuellen Stunde. '
                    f'Abgelaufene Eintraäge wurden entfernt: {tariff_state.prices}')
        return tariff_state


class ConfigurableFlexibleTariff(ConfigurableTariff):
    def __init__(self,
                 config: T_TARIFF_CONFIG,
                 component_initializer: Callable[[], float]) -> None:
        self.store = store.get_flexible_tariff_value_store()
        self.fault_state = FaultState(ComponentInfo(None, config.name, ComponentType.FLEXIBLE_TARIFF.value))
        super().__init__(config, component_initializer)


class ConfigurableGridFee(ConfigurableTariff):
    def __init__(self,
                 config: T_TARIFF_CONFIG,
                 component_initializer: Callable[[], float]) -> None:
        self.store = store.get_grid_fee_value_store()
        self.fault_state = FaultState(ComponentInfo(None, config.name, ComponentType.GRID_FEE.value))
        super().__init__(config, component_initializer)
