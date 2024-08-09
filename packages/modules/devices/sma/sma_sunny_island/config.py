from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class SmaSunnyIslandConfiguration:
    def __init__(self, ip_address: Optional[str] = None, port: int = 502):
        self.ip_address = ip_address
        self.port = port


class SmaSunnyIsland:
    def __init__(self,
                 name: str = "SMA Sunny Island, Sunny Tripower X",
                 type: str = "sma_sunny_island",
                 id: int = 0,
                 configuration: SmaSunnyIslandConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or SmaSunnyIslandConfiguration()


class SmaSunnyIslandBatConfiguration:
    def __init__(self, modbus_id: int = 3):
        self.modbus_id = modbus_id


class SmaSunnyIslandBatSetup(ComponentSetup[SmaSunnyIslandBatConfiguration]):
    def __init__(self,
                 name: str = "SMA Sunny Island Speicher, Sunny Tripower X",
                 type: str = "bat",
                 id: int = 0,
                 configuration: SmaSunnyIslandBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SmaSunnyIslandBatConfiguration())
