from typing import Optional
from helpermodules.auto_str import auto_str
from modules.common.component_setup import ComponentSetup

from ..vendor import vendor_descriptor


@auto_str
class CHINTConfiguration:
    def __init__(self, ip_address: Optional[str] = None, port: int = 8899):
        self.ip_address = ip_address
        self.port = port


@auto_str
class CHINT:
    def __init__(self,
                 name: str = "CHINT",
                 type: str = "chint",
                 id: int = 0,
                 configuration: CHINTConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or CHINTConfiguration()


@auto_str
class CHINTCounterConfiguration:
    def __init__(self, modbus_id: int = 1, invert: bool = False):
        self.modbus_id = modbus_id
        self.invert = invert


@auto_str
class CHINTCounterSetup(ComponentSetup[CHINTCounterConfiguration]):
    def __init__(self,
                 name: str = "CHINT DTSU666 Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: CHINTCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or CHINTCounterConfiguration())
