from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class AlgodueConfiguration:
    def __init__(self, modbus_id: int = 1, ip_address: Optional[str] = None, port: int = 502):
        self.modbus_id = modbus_id
        self.ip_address = ip_address
        self.port = port


class Algodue:
    def __init__(self,
                 name: str = "Algodue",
                 type: str = "Algodue",
                 id: int = 0,
                 configuration: AlgodueConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or AlgodueConfiguration()


class AlgodueCounterConfiguration:
    def __init__(self):
        pass


class AlgodueCounterSetup(ComponentSetup[AlgodueCounterConfiguration]):
    def __init__(self,
                 name: str = "Algodue Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: AlgodueCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or AlgodueCounterConfiguration())
