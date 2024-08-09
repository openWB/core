from typing import Optional

from helpermodules.auto_str import auto_str
from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class FoxEssConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: int = 502):
        self.ip_address = ip_address
        self.port = port


class FoxEss:
    def __init__(self,
                 name: str = "FoxESS",
                 type: str = "fox_ess",
                 id: int = 0,
                 configuration: FoxEssConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or FoxEssConfiguration()


@auto_str
class FoxEssBatConfiguration:
    def __init__(self, modbus_id: int = 1):
        self.modbus_id = modbus_id


@auto_str
class FoxEssBatSetup(ComponentSetup[FoxEssBatConfiguration]):
    def __init__(self,
                 name: str = "FoxESS Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: FoxEssBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or FoxEssBatConfiguration())


@auto_str
class FoxEssCounterConfiguration:
    def __init__(self, modbus_id: int = 1):
        self.modbus_id = modbus_id


@auto_str
class FoxEssCounterSetup(ComponentSetup[FoxEssCounterConfiguration]):
    def __init__(self,
                 name: str = "FoxESS Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: FoxEssCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or FoxEssCounterConfiguration())


@auto_str
class FoxEssInverterConfiguration:
    def __init__(self, modbus_id: int = 1):
        self.modbus_id = modbus_id


@auto_str
class FoxEssInverterSetup(ComponentSetup[FoxEssInverterConfiguration]):
    def __init__(self,
                 name: str = "FoxESS Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: FoxEssInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or FoxEssInverterConfiguration())
