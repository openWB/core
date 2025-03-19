from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor
from modules.devices.growatt.growatt.version import GrowattVersion


class GrowattConfiguration:
    def __init__(self, modbus_id: int = 1,
                 ip_address: Optional[str] = None,
                 port: int = 502,
                 version: GrowattVersion = GrowattVersion.max_series):
        self.modbus_id = modbus_id
        self.ip_address = ip_address
        self.port = port
        self.version = version


class Growatt:
    def __init__(self,
                 name: str = "Growatt",
                 type: str = "growatt",
                 id: int = 0,
                 configuration: GrowattConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or GrowattConfiguration()


class GrowattBatConfiguration:
    def __init__(self):
        pass


class GrowattBatSetup(ComponentSetup[GrowattBatConfiguration]):
    def __init__(self,
                 name: str = "Growatt Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: GrowattBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or GrowattBatConfiguration())


class GrowattCounterConfiguration:
    def __init__(self):
        pass


class GrowattCounterSetup(ComponentSetup[GrowattCounterConfiguration]):
    def __init__(self,
                 name: str = "Growatt Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: GrowattCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or GrowattCounterConfiguration())


class GrowattInverterConfiguration:
    def __init__(self):
        pass


class GrowattInverterSetup(ComponentSetup[GrowattInverterConfiguration]):
    def __init__(self,
                 name: str = "Growatt Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: GrowattInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or GrowattInverterConfiguration())
