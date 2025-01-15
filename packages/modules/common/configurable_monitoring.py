from typing import Callable

from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_type import ComponentType
from modules.common.fault_state import ComponentInfo, FaultState


class ConfigurableMonitoring():
    def __init__(self,
                 start_initializer: Callable[[]],
                 stop_initializer: Callable[[]]) -> None:
        self.fault_state = FaultState(ComponentInfo(None, self.config.name, ComponentType.ELECTRICITY_TARIFF.value))
        with SingleComponentUpdateContext(self.fault_state):
            self._start_monitoring = start_initializer()
            self._stop_monitoring = stop_initializer()

    def start_monitoring(self):
        self._start_monitoring()

    def stop_monitoring(self):
        self._stop_monitoring()
