import logging
from typing import Dict, Optional, TypeVar, Generic, Callable, Union

from helpermodules.pub import Pub
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
                 component_writer: Callable[[Dict[int, Union[float, int]]], Optional[IoState]],
                 initializer: Callable = lambda: None) -> None:
        self.config = config
        self.fault_state = FaultState(ComponentInfo(self.config.id, self.config.name,
                                      ComponentType.IO.value))
        self.store = store.get_io_value_store(self.config.id)
        self.set_manual: Dict = {"analog_output": {}, "digital_output": {}}
        with SingleComponentUpdateContext(self.fault_state):
            self.component_reader = component_reader
            self.component_writer = component_writer
            initializer()

    def read(self):
        if hasattr(self, "component_reader"):
            # Wenn beim Initialisieren etwas schief gelaufen ist, ursprüngliche Fehlermeldung beibehalten
            with SingleComponentUpdateContext(self.fault_state):
                io_state = self.component_reader()
                self.store.set(io_state)

    def update_manual_output(self, manual: Dict[str, bool], output: Dict[str, bool], string: str, topic_suffix: str):
        if len(manual) > 0:
            log.debug(f"Manuell gesetzte {string} Ausgänge: {manual}")
            for manual_out_pin, manual_out_value in manual.items():
                output[manual_out_pin] = manual_out_value
                # nur die in diesem Zyklus gesetzten manuellen Ausgänge setzen, für nächsten Zyklus zurücksetzen
                Pub().pub(f"openWB/set/io/{self.config.id}/set/manual/{topic_suffix}/{manual_out_pin}", "")

    def write(self, analog_output, digital_output):
        if hasattr(self, "component_writer"):
            # Wenn beim Initialisieren etwas schief gelaufen ist, ursprüngliche Fehlermeldung beibehalten
            with SingleComponentUpdateContext(self.fault_state):
                self.update_manual_output(self.set_manual["analog_output"], analog_output, "analoge", "analog_output")
                self.update_manual_output(self.set_manual["digital_output"],
                                          digital_output, "digitale", "digital_output")
                if ((analog_output and self.store.delegate.state.analog_output != analog_output) or
                        (digital_output and self.store.delegate.state.digital_output != digital_output)):
                    io_state = self.component_writer(analog_output, digital_output)
                    if io_state is not None:
                        self.store.set(io_state)
