from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class AnkerConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: int = 502,
                 modbus_id: int = 1):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id


class Anker:
    def __init__(self,
                 name: str = "Anker SOLIX Solarbank Max AC",
                 type: str = "solarbank_max_ac",
                 id: int = 0,
                 configuration: AnkerConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or AnkerConfiguration()


class AnkerBatConfiguration:
    def __init__(self):
        pass


class AnkerBatSetup(ComponentSetup[AnkerBatConfiguration]):
    def __init__(self,
                 name: str = "Anker Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: AnkerBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or AnkerBatConfiguration())


class AnkerInverterConfiguration:
    def __init__(self):
        pass


class AnkerInverterSetup(ComponentSetup[AnkerInverterConfiguration]):
    def __init__(self,
                 name: str = "Anker Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: AnkerInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or AnkerInverterConfiguration())
