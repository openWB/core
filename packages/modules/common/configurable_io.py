import logging
from typing import Dict, Optional, TypeVar, Generic, Callable, Union

from modules.common import store
from modules.common.abstract_io import AbstractIoDevice
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import IoState
from modules.common.component_type import ComponentType
from modules.common.fault_state import ComponentInfo, FaultState


T_IO_CONFIG = TypeVar("T_IO_CONFIG")
log = logging.getLogger(__name__)


class ConfigurableIo(Generic[T_IO_CONFIG], AbstractIoDevice):
    def __init__(self,
                 config: T_IO_CONFIG,
                 component_reader: Callable[[], IoState],
                 component_writer: Callable[[Dict[int, Union[float, int]]], Optional[IoState]]) -> None:
        self.config = config
        self.fault_state = FaultState(ComponentInfo(self.config.id, self.config.name,
                                      ComponentType.IO.value))
        self.store = store.get_io_value_store(self.config.id)
        self.set_manual: Dict = {}
        with SingleComponentUpdateContext(self.fault_state):
            self.component_reader = component_reader
            self.component_writer = component_writer

    def read(self):
        if hasattr(self, "component_reader"):
            # Wenn beim Initialisieren etwas schief gelaufen ist, ursprüngliche Fehlermeldung beibehalten
            with SingleComponentUpdateContext(self.fault_state):
                io_state = self.component_reader()
                if len(self.set_manual) > 0:
                    log.debug(f"Manuell gesetzte Ausgänge: {self.set_manual}")
                for manual_output_topic, manual_output_payload in self.set_manual.items():
                    splitted_topic = manual_output_topic.split("/")
                    output = io_state.getattr(splitted_topic[-2])
                    output.setattr(splitted_topic[-1], manual_output_payload)
                self.set_manual.clear()
                self.store.set(io_state)

    def write(self, analog_output, digital_output):
        if hasattr(self, "component_writer"):
            # Wenn beim Initialisieren etwas schief gelaufen ist, ursprüngliche Fehlermeldung beibehalten
            with SingleComponentUpdateContext(self.fault_state):
                if ((analog_output and self.store.delegate.state.analog_output != analog_output) or
                        (digital_output and self.store.delegate.state.digital_output != digital_output)):
                    io_state = self.component_writer(analog_output, digital_output)
                    if io_state is not None:
                        self.store.set(io_state)
