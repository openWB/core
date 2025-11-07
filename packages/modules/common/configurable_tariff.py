from typing import TypeVar, Generic, Callable
from helpermodules import timecheck
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


class ConfigurableElectricityTariff(Generic[T_TARIFF_CONFIG]):
    def __init__(self,
                 config: T_TARIFF_CONFIG,
                 component_initializer: Callable[[], float]) -> None:
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
                tariff_state, timeslot_length_seconds = self.__update_et_provider_data()
                self.__store_and_publish_updated_data(tariff_state)
                self.__log_and_publish_progress(timeslot_length_seconds, tariff_state)

    def __update_et_provider_data(self) -> tuple[TariffState, int]:
        tariff_state = self._component_updater()
        timeslot_length_seconds = self.__calculate_price_timeslot_length(tariff_state)
        tariff_state = self._remove_outdated_prices(tariff_state, timeslot_length_seconds)
        return tariff_state, timeslot_length_seconds

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
            for timestamp in list(tariff_state.prices.keys()):
                if int(timestamp) < now - (timeslot_length_seconds - 1):  # keep current time slot
                    tariff_state.prices.pop(timestamp)
                    log.debug(
                        'Die Preisliste startet nicht mit der aktuellen Stunde. '
                        f'Eintrag {timestamp} wurden entfernt. rest: {tariff_state.prices}')
        return tariff_state
