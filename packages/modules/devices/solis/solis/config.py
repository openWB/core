from typing import Optional
from helpermodules.auto_str import auto_str

from modules.common.component_setup import ComponentSetup
from modules.devices.solis.solis.version import SolisVersion
from ..vendor import vendor_descriptor


class SolisConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: int = 502,
                 version: SolisVersion = SolisVersion.hybrid):
        self.ip_address = ip_address
        self.port = port
        self.version = version


class Solis:
    def __init__(self,
                 name: str = "Solis",
                 type: str = "solis",
                 id: int = 0,
                 configuration: SolisConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or SolisConfiguration()


@auto_str
class SolisBatConfiguration:
    def __init__(self, modbus_id: int = 1):
        self.modbus_id = modbus_id


@auto_str
class SolisBatSetup(ComponentSetup[SolisBatConfiguration]):
    def __init__(self,
                 name: str = "Solis Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: SolisBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SolisBatConfiguration())


@auto_str
class SolisCounterConfiguration:
    def __init__(self, modbus_id: int = 1):
        self.modbus_id = modbus_id


@auto_str
class SolisCounterSetup(ComponentSetup[SolisCounterConfiguration]):
    def __init__(self,
                 name: str = "Solis Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: SolisCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SolisCounterConfiguration())


@auto_str
class SolisInverterConfiguration:
    def __init__(self, modbus_id: int = 1):
        self.modbus_id = modbus_id


@auto_str
class SolisInverterSetup(ComponentSetup[SolisInverterConfiguration]):
    def __init__(self,
                 name: str = "Solis Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: SolisInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SolisInverterConfiguration())
