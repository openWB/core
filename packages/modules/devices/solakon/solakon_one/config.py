from typing import Optional

from helpermodules.auto_str import auto_str
from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class SolakonOneConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: int = 502):
        self.ip_address = ip_address
        self.port = port


class SolakonOne:
    def __init__(self,
                 name: str = "Solakon One",
                 type: str = "solakon_one",
                 id: int = 0,
                 configuration: SolakonOneConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or SolakonOneConfiguration()


@auto_str
class SolakonOneBatConfiguration:
    def __init__(self, modbus_id: int = 1):
        self.modbus_id = modbus_id


@auto_str
class SolakonOneBatSetup(ComponentSetup[SolakonOneBatConfiguration]):
    def __init__(self,
                 name: str = "Solakon One Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: SolakonOneBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SolakonOneBatConfiguration())


@auto_str
class SolakonOneInverterConfiguration:
    def __init__(self, modbus_id: int = 1):
        self.modbus_id = modbus_id


@auto_str
class SolakonOneInverterSetup(ComponentSetup[SolakonOneInverterConfiguration]):
    def __init__(self,
                 name: str = "Solakon One Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: SolakonOneInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SolakonOneInverterConfiguration())
