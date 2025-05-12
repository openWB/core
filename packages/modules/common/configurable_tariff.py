from typing import TypeVar, Generic, Callable
from helpermodules.timecheck import create_unix_timestamp_current_full_hour

from modules.common import store
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import TariffState
from modules.common.component_type import ComponentType
from modules.common.fault_state import ComponentInfo, FaultState


T_TARIFF_CONFIG = TypeVar("T_TARIFF_CONFIG")


class ConfigurableElectricityTariff(Generic[T_TARIFF_CONFIG]):
    def __init__(self,
                 config: T_TARIFF_CONFIG,
                 component_initializer: Callable[[], float]) -> None:
        self.config = config
        self.store = store.get_electricity_tariff_value_store()
        self.fault_state = FaultState(ComponentInfo(None, self.config.name, ComponentType.ELECTRICITY_TARIFF.value))
        with SingleComponentUpdateContext(self.fault_state):
            self._component_updater = component_initializer(config)

    def update(self):
        if hasattr(self, "_component_updater"):
            # Wenn beim Initialisieren etwas schief gelaufen ist, ursprüngliche Fehlermeldung beibehalten
            with SingleComponentUpdateContext(self.fault_state):
                tariff_state = self._remove_outdated_prices(self._component_updater())
                self.store.set(tariff_state)
                self.store.update()
                if len(tariff_state.prices) < 24:
                    self.fault_state.no_error(
                        f'Die Preisliste hat nicht 24, sondern {len(tariff_state.prices)} Einträge. '
                        'Die Strompreise werden vom Anbieter erst um 14:00 für den Folgetag aktualisiert.')

    def _remove_outdated_prices(self, tariff_state: TariffState) -> TariffState:
        current_hour = str(int(create_unix_timestamp_current_full_hour()))
        for timestamp in list(tariff_state.prices.keys()):
            if timestamp < current_hour:
                self.fault_state.warning(
                    'Die Preisliste startet nicht mit der aktuellen Stunde. Abgelaufene Einträge wurden entfernt.')
                tariff_state.prices.pop(timestamp)
        return tariff_state
