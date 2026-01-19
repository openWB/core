from typing import Optional
from helpermodules.auto_str import auto_str
from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


@auto_str
class SolvisConfiguration:
    def __init__(self, ip_address: Optional[str] = None, port: int = 502, modbus_id: int = 1):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id


@auto_str
class Solvis:
    def __init__(self,
                 name: str = "Solvis",
                 type: str = "solvis",
                 id: int = 0,
                 configuration: SolvisConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or SolvisConfiguration()


@auto_str
class SolvisCounterConfiguration:
    def __init__(self):
        pass


@auto_str
class SolvisCounterSetup(ComponentSetup[SolvisCounterConfiguration]):
    def __init__(self,
                 name: str = "Solvis Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: SolvisCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SolvisCounterConfiguration())
