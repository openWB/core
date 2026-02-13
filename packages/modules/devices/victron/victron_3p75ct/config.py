from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class VictronConfiguration:
    def __init__(self, ip_address: Optional[str] = None, port: int = 502):
        self.ip_address = ip_address
        self.port = port


class Victron:
    def __init__(self,
                 name: str = "Victron 3P75CT",
                 type: str = "victron_3p75ct",
                 id: int = 0,
                 configuration: VictronConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or VictronConfiguration()


class VictronCounterConfiguration:
    def __init__(self):
        pass


class VictronCounterSetup(ComponentSetup[VictronCounterConfiguration]):
    def __init__(self,
                 name: str = "Victron Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: VictronCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or VictronCounterConfiguration())
