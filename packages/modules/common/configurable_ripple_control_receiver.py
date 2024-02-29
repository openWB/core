from typing import TypeVar, Generic, Callable

from modules.common import store
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_type import ComponentType
from modules.common.fault_state import ComponentInfo, FaultState


T_RCR_CONFIG = TypeVar("T_RCR_CONFIG")


class ConfigurableRcr(Generic[T_RCR_CONFIG]):
    def __init__(self,
                 config: T_RCR_CONFIG,
                 component_updater: Callable[[], float]) -> None:
        self.__component_updater = component_updater
        self.config = config
        self.fault_state = FaultState(ComponentInfo(None, self.config.name,
                                      ComponentType.RIPPLE_CONTROL_RECEIVER.value))
        self.store = store.get_ripple_control_receiver_value_store()

    def update(self):
        with SingleComponentUpdateContext(self.fault_state):
            self.store.set(self.__component_updater())
