from typing import Optional
from helpermodules.auto_str import auto_str

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class DeyeConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: int = 8899):
        self.ip_address = ip_address
        self.port = port


class Deye:
    def __init__(self,
                 name: str = "Deye/Jinko (Anbindung per Modbus)",
                 type: str = "deye",
                 id: int = 0,
                 configuration: DeyeConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or DeyeConfiguration()


@auto_str
class DeyeBatConfiguration:
    def __init__(self, modbus_id: int = 1):
        self.modbus_id = modbus_id


@auto_str
class DeyeBatSetup(ComponentSetup[DeyeBatConfiguration]):
    def __init__(self,
                 name: str = "Deye/Jinko Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: DeyeBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or DeyeBatConfiguration())


@auto_str
class DeyeCounterConfiguration:
    def __init__(self, modbus_id: int = 1):
        self.modbus_id = modbus_id


@auto_str
class DeyeCounterSetup(ComponentSetup[DeyeCounterConfiguration]):
    def __init__(self,
                 name: str = "Deye/Jinko Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: DeyeCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or DeyeCounterConfiguration())


@auto_str
class DeyeInverterConfiguration:
    def __init__(self, modbus_id: int = 1):
        self.modbus_id = modbus_id


@auto_str
class DeyeInverterSetup(ComponentSetup[DeyeInverterConfiguration]):
    def __init__(self,
                 name: str = "Deye/Jinko Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: DeyeInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or DeyeInverterConfiguration())
