from typing import Optional

from helpermodules.auto_str import auto_str
from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class FoxEssH3SmartConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: int = 502):
        self.ip_address = ip_address
        self.port = port


class FoxEssH3Smart:
    def __init__(self,
                 name: str = "FoxEss H3 Smart",
                 type: str = "fox_ess_h3_smart",
                 id: int = 0,
                 configuration: FoxEssH3SmartConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or FoxEssH3SmartConfiguration()


@auto_str
class FoxEssH3SmartBatConfiguration:
    def __init__(self, modbus_id: int = 247):
        self.modbus_id = modbus_id


@auto_str
class FoxEssH3SmartBatSetup(ComponentSetup[FoxEssH3SmartBatConfiguration]):
    def __init__(self,
                 name: str = "FoxEss H3 Smart Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: FoxEssH3SmartBatConfiguration = None,
                 **kwargs) -> None:
        super().__init__(name, type, id, configuration or FoxEssH3SmartBatConfiguration(), **kwargs)


@auto_str
class FoxEssH3SmartCounterConfiguration:
    def __init__(self, modbus_id: int = 247):
        self.modbus_id = modbus_id


@auto_str
class FoxEssH3SmartCounterSetup(ComponentSetup[FoxEssH3SmartCounterConfiguration]):
    def __init__(self,
                 name: str = "FoxEss H3 Smart Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: FoxEssH3SmartCounterConfiguration = None,
                 **kwargs) -> None:
        super().__init__(name, type, id, configuration or FoxEssH3SmartCounterConfiguration(), **kwargs)


@auto_str
class FoxEssH3SmartInverterConfiguration:
    def __init__(self, modbus_id: int = 247):
        self.modbus_id = modbus_id


@auto_str
class FoxEssH3SmartInverterSetup(ComponentSetup[FoxEssH3SmartInverterConfiguration]):
    def __init__(self,
                 name: str = "FoxEss H3 Smart Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: FoxEssH3SmartInverterConfiguration = None,
                 **kwargs) -> None:
        super().__init__(name, type, id, configuration or FoxEssH3SmartInverterConfiguration(), **kwargs)
