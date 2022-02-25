import logging
from typing import Dict

from modules.common.abstract_device import AbstractDevice
from modules.common.component_context import SingleComponentUpdateContext
from modules.virtual import counter

log = logging.getLogger(__name__)


def get_default_config() -> dict:
    return {
        "name": "Virtuelles Gerät",
        "type": "virtual",
        "id": 0,
        "configuration":
        {
        }
    }


class Device(AbstractDevice):
    COMPONENT_TYPE_TO_CLASS = {
        "counter": counter.VirtualCounter
    }

    def __init__(self, device_config: dict) -> None:
        self.components = {}  # type: Dict[str, counter.VirtualCounter]
        try:
            self.device_config = device_config
        except Exception:
            log.exception("Fehler im Modul " + device_config["name"])

    def add_component(self, component_config: dict) -> None:
        component_type = component_config["type"]
        if component_type in self.COMPONENT_TYPE_TO_CLASS:
            self.components["component"+str(component_config["id"])] = (self.COMPONENT_TYPE_TO_CLASS[component_type](
                self.device_config["id"], component_config))

    def get_values(self) -> None:
        log.debug("Start device reading" + str(self.components))
        if self.components:
            for component in self.components:
                # Auch wenn bei einer Komponente ein Fehler auftritt, sollen alle anderen noch ausgelesen werden.
                with SingleComponentUpdateContext(self.components[component].component_info):
                    self.components[component].update()
        else:
            log.warning(
                self.device_config["name"] +
                ": Es konnten keine Werte gelesen werden, da noch keine Komponenten konfiguriert wurden."
            )
