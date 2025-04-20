from typing import Optional
from helpermodules.auto_str import auto_str
from modules.common.component_setup import ComponentSetup

from ..vendor import vendor_descriptor

@auto_str
class ThermiaConfiguration:
    def __init__(self, ip_address: Optional[str] = None, port: int = 502):
        self.ip_address = ip_address
        self.port = port


@auto_str
class Thermia:
    def __init__(self,
                 name: str = "Thermia",
                 type: str = "thermia",
                 id: int = 0,
                 configuration: ThermiaConfiguration = None) -> None:
        self.name = name
        self.type = type

        self.vendor = vendor_descriptor.configuration_factory().type

        self.id = id
        self.configuration = configuration or ThermiaConfiguration()


@auto_str
class ThermiaCounterConfiguration:
    def __init__(self, modbus_id: int = 1):
        self.modbus_id = modbus_id


@auto_str
class ThermiaCounterSetup(ComponentSetup[ThermiaCounterConfiguration]):
    def __init__(self,
                 name: str = "Thermia Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: ThermiaCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or ThermiaCounterConfiguration())
