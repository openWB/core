from typing import Optional
from helpermodules.auto_str import auto_str
from modules.common.component_setup import ComponentSetup

from ..vendor import vendor_descriptor


@auto_str
class ZCSConfiguration:
    def __init__(self, ip_address: Optional[str] = None, port: int = 8899):
        self.ip_address = ip_address
        self.port = port


@auto_str
class ZCS:
    def __init__(self,
                 name: str = "ZCS",
                 type: str = "zcs",
                 id: int = 0,
                 configuration: ZCSConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or ZCSConfiguration()


@auto_str
class ZCSInverterConfiguration:
    def __init__(self, modbus_id: int = 1):
        self.modbus_id = modbus_id


@auto_str
class ZCSInverterSetup(ComponentSetup[ZCSInverterConfiguration]):
    def __init__(self,
                 name: str = "ZCS Azzurro 3PH 12KTL Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: ZCSInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or ZCSInverterConfiguration())
