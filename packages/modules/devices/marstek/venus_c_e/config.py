from typing import Optional
from helpermodules.auto_str import auto_str
from modules.common.component_setup import ComponentSetup

from ..vendor import vendor_descriptor


@auto_str
class VenusCEConfiguration:
    def __init__(self, ip_address: Optional[str] = None, port: int = 502):
        self.ip_address = ip_address
        self.port = port


@auto_str
class VenusCE:
    def __init__(self,
                 name: str = "Marstek Venus C, E",
                 type: str = "venus_c_e",
                 id: int = 0,
                 configuration: VenusCEConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or VenusCEConfiguration()


@auto_str
class VenusCEBatConfiguration:
    def __init__(self, modbus_id: int = 1):
        self.modbus_id = modbus_id


@auto_str
class VenusCEBatSetup(ComponentSetup[VenusCEBatConfiguration]):
    def __init__(self,
                 name: str = "Marstek Venus C, E Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: VenusCEBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or VenusCEBatConfiguration())
