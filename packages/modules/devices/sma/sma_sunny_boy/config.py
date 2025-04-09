from typing import Optional

from modules.common.component_setup import ComponentSetup
from modules.devices.sma.sma_sunny_boy.inv_version import SmaInverterVersion
from ..vendor import vendor_descriptor


class SmaSunnyBoyConfiguration:
    def __init__(self, ip_address: Optional[str] = None, port: int = 502):
        self.ip_address = ip_address
        self.port = port


class SmaSunnyBoy:
    def __init__(self,
                 name: str = "SMA Sunny Boy/Tripower, Tesvolt",
                 type: str = "sma_sunny_boy",
                 id: int = 0,
                 configuration: SmaSunnyBoyConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or SmaSunnyBoyConfiguration()


class SmaSunnyBoyBatConfiguration:
    def __init__(self, modbus_id: int = 3):
        self.modbus_id = modbus_id


class SmaSunnyBoyBatSetup(ComponentSetup[SmaSunnyBoyBatConfiguration]):
    def __init__(self,
                 name: str = "Sma Sunny Boy/Tripower Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: SmaSunnyBoyBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SmaSunnyBoyBatConfiguration())


class SmaSunnyBoySmartEnergyBatConfiguration:
    def __init__(self, modbus_id: int = 3):
        self.modbus_id = modbus_id


class SmaSunnyBoySmartEnergyBatSetup(ComponentSetup[SmaSunnyBoySmartEnergyBatConfiguration]):
    def __init__(self,
                 name: str = "Sma Sunny Boy Smart Energy Speicher",
                 type: str = "bat_smart_energy",
                 id: int = 0,
                 configuration: SmaSunnyBoySmartEnergyBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SmaSunnyBoySmartEnergyBatConfiguration())


class SmaTesvoltBatConfiguration:
    def __init__(self):
        pass


class SmaTesvoltBatSetup(ComponentSetup[SmaTesvoltBatConfiguration]):
    def __init__(self,
                 name: str = "Sma Tripower/Tesvolt Speicher",
                 type: str = "bat_tesvolt",
                 id: int = 0,
                 configuration: SmaTesvoltBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SmaTesvoltBatConfiguration())


class SmaSunnyBoyCounterConfiguration:
    def __init__(self, modbus_id: int = 3):
        self.modbus_id = modbus_id


class SmaSunnyBoyCounterSetup(ComponentSetup[SmaSunnyBoyCounterConfiguration]):
    def __init__(self,
                 name: str = "Sma Sunny Boy/Tripower Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: SmaSunnyBoyCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SmaSunnyBoyCounterConfiguration())


class SmaSunnyBoyInverterConfiguration:
    def __init__(self, hybrid: bool = False,
                 version: SmaInverterVersion = SmaInverterVersion.default,
                 modbus_id: int = 3):
        self.hybrid = hybrid
        self.version = version
        self.modbus_id = modbus_id


class SmaSunnyBoyInverterSetup(ComponentSetup[SmaSunnyBoyInverterConfiguration]):
    def __init__(self,
                 name: str = "Sma Sunny Boy/Tripower Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: SmaSunnyBoyInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SmaSunnyBoyInverterConfiguration())
