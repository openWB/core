import logging
from typing import Any, TypeVar, Generic, Callable, Optional, Union, TypedDict

from modules.common.component_context import SingleComponentUpdateContext
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import ValueStore
from modules.devices.sma.sma_shm.config import SmaHomeManagerCounterSetup, SmaHomeManagerInverterSetup

T = TypeVar("T")
log = logging.getLogger(__name__)


def _create_serial_matcher(serial: Optional[int]) -> Callable[[dict], bool]:
    if isinstance(serial, int):
        return lambda sma_data: sma_data["serial"] == serial
    if serial is not None:
        log.error("Serial <%s> must be an int or None, but is <%s>. Assuming None.", serial, type(serial))
    return lambda _: True


class KwargsDict(TypedDict):
    value_store_factory: Callable[[int], ValueStore[T]]
    parser: Callable[[dict], T]


class SpeedwireComponent(Generic[T]):
    def __init__(self,
                 component_config: Union[SmaHomeManagerCounterSetup, SmaHomeManagerInverterSetup],
                 **kwargs: Any):
        self.kwargs: KwargsDict = kwargs
        self.component_config = component_config

    def initialize(self) -> None:
        self.store = self.kwargs['value_store_factory'](self.component_config.type, self.component_config.id)
        self.__parser = self.kwargs['parser']
        self.__serial_matcher = _create_serial_matcher(self.component_config.configuration.serials)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def read_datagram(self, datagram: dict) -> bool:
        if self.__serial_matcher(datagram):
            with SingleComponentUpdateContext(self.fault_state):
                self.store.set(self.__parser(datagram))
            return True
        return False
