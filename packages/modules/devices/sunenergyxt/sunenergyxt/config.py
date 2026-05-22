from typing import Optional
from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class SunEnergyXTConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = "192.168.1.100",
                 port: int = 80,
                 timeout: int = 5):
        self.ip_address = ip_address
        self.port = port
        self.timeout = timeout


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
