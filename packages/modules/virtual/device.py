import logging
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.virtual.config import Virtual, VirtualCounterSetup
from modules.common.abstract_device import AbstractDevice, DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.virtual import counter

log = logging.getLogger(__name__)


class Device(AbstractDevice):
    COMPONENT_TYPE_TO_CLASS = {
        "counter": counter.VirtualCounter
    }
    COMPONENT_TYPE_TO_MODULE = {
        "counter": counter
    }

    def __init__(self, device_config: Union[Dict, Virtual]) -> None:
        self.components = {}  # type: Dict[str, counter.VirtualCounter]
        try:
            self.device_config = dataclass_from_dict(Virtual, device_config)
        except Exception:
            log.exception("Fehler im Modul " + self.device_config.name)

    def add_component(self, component_config: Union[Dict, VirtualCounterSetup]) -> None:
        if isinstance(component_config, Dict):
            component_type = component_config["type"]
        else:
            component_type = component_config.type
        component_config = dataclass_from_dict(self.COMPONENT_TYPE_TO_MODULE[
            component_type].component_descriptor.configuration_factory, component_config)
        if component_type in self.COMPONENT_TYPE_TO_CLASS:
            self.components["component"+str(component_config.id)] = (self.COMPONENT_TYPE_TO_CLASS[component_type](
                self.device_config.id, component_config))

    def update(self) -> None:
        log.debug("Start device reading" + str(self.components))
        if self.components:
            for component in self.components:
                # Auch wenn bei einer Komponente ein Fehler auftritt, sollen alle anderen noch ausgelesen werden.
                with SingleComponentUpdateContext(self.components[component].component_info):
                    self.components[component].update()
        else:
            log.warning(
                self.device_config.name +
                ": Es konnten keine Werte gelesen werden, da noch keine Komponenten konfiguriert wurden."
            )


device_descriptor = DeviceDescriptor(configuration_factory=Virtual)
