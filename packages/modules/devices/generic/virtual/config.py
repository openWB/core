from modules.common.component_setup import ComponentSetup
from typing import List


class VirtualConfiguration:
    def __init__(self):
        pass


class Virtual:
    def __init__(self,
                 name: str = "Virtuelles Gerät",
                 type: List[str] = ["generic", "virtual"],
                 group: str = "generic",
                 id: int = 0,
                 configuration: VirtualConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.group = group
        self.id = id
        self.configuration = configuration or VirtualConfiguration()


class VirtualCounterConfiguration:
    def __init__(self, external_consumption=0):
        self.external_consumption = external_consumption


class VirtualCounterSetup(ComponentSetup[VirtualCounterConfiguration]):
    def __init__(self,
                 name: str = "Virtueller Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: VirtualCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or VirtualCounterConfiguration())
