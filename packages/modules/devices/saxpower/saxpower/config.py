from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class SaxpowerConfiguration:
    def __init__(self, modbus_id: int = 64, ip_address: Optional[str] = None, port: int = 3600):
        self.modbus_id = modbus_id
        self.ip_address = ip_address
        self.port = port


class Saxpower:
    def __init__(self,
                 name: str = "Saxpower",
                 type: str = "saxpower",
                 id: int = 0,
                 configuration: SaxpowerConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or SaxpowerConfiguration()


class SaxpowerBatConfiguration:
    def __init__(self):
        pass


class SaxpowerBatSetup(ComponentSetup[SaxpowerBatConfiguration]):
    def __init__(self,
                 name: str = "Saxpower Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: SaxpowerBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SaxpowerBatConfiguration())
