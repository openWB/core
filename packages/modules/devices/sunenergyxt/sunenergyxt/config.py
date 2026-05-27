from typing import Optional
from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class SunEnergyXTConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None):
        self.ip_address = ip_address


class SunEnergyXT:
    def __init__(self,
                 name: str = "SunEnergyXT 500 Series",
                 type: str = "sunenergyxt",
                 id: int = 0,
                 configuration: SunEnergyXTConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or SunEnergyXTConfiguration()


class SunEnergyXTBatConfiguration:
    def __init__(self):
        pass


class SunEnergyXTBatSetup(ComponentSetup[SunEnergyXTBatConfiguration]):
    def __init__(self,
                 name: str = "SunEnergyXT Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: SunEnergyXTBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SunEnergyXTBatConfiguration())
