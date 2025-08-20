from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class MarstekConfiguration:
    def __init__(self, modbus_id: int = 1, ip_address: Optional[str] = None, port: int = 3600):
        self.modbus_id = modbus_id
        self.ip_address = ip_address
        self.port = port


class Marstek:
    def __init__(self,
                 name: str = "marstek",
                 type: str = "marstek",
                 id: int = 0,
                 configuration: MarstekConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or MarstekConfiguration()


class MarstekBatConfiguration:
    def __init__(self):
        pass


class MarstekBatSetup(ComponentSetup[MarstekBatConfiguration]):
    def __init__(self,
                 name: str = "Marstek Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: MarstekBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or MarstekBatConfiguration())
