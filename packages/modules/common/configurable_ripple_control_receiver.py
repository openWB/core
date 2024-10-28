from typing import TypeVar, Generic, Callable

from modules.common import store
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_type import ComponentType
from modules.common.fault_state import ComponentInfo, FaultState


T_RCR_CONFIG = TypeVar("T_RCR_CONFIG")


class ConfigurableRcr(Generic[T_RCR_CONFIG]):
    def __init__(self,
                 config: T_RCR_CONFIG,
                 component_initializer: Callable[[], float]) -> None:
        self.config = config
        self.fault_state = FaultState(ComponentInfo(None, self.config.name,
                                      ComponentType.RIPPLE_CONTROL_RECEIVER.value))
        with SingleComponentUpdateContext(self.fault_state):
            self._component_updater = component_initializer(config)
        self.store = store.get_ripple_control_receiver_value_store()

    def update(self):
        if hasattr(self, "_component_updater"):
            # Wenn beim Initialisieren etwas schief gelaufen ist, ursprüngliche Fehlermeldung beibehalten
            with SingleComponentUpdateContext(self.fault_state):
                self.store.set(self._component_updater())
