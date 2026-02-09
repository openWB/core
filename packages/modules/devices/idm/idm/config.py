from typing import Optional
from helpermodules.auto_str import auto_str
from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


@auto_str
class IDMConfiguration:
    def __init__(self, ip_address: Optional[str] = None, port: int = 502, modbus_id: int = 1):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id


@auto_str
class IDM:
    def __init__(self,
                 name: str = "IDM",
                 type: str = "idm",
                 id: int = 0,
                 configuration: IDMConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or IDMConfiguration()


@auto_str
class IDMCounterConfiguration:
    def __init__(self):
        pass


@auto_str
class IDMCounterSetup(ComponentSetup[IDMCounterConfiguration]):
    def __init__(self,
                 name: str = "IDM Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: IDMCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or IDMCounterConfiguration())
