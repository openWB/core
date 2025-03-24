from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class UPowerConfiguration:
    def __init__(self, modbus_id: int = 1, ip_address: Optional[str] = None, port: int = 502, version: int = 1):
        self.modbus_id = modbus_id
        self.ip_address = ip_address
        self.port = port
        self.version = version


class UPower:
    def __init__(self,
                 name: str = "UPower",
                 type: str = "upower",
                 id: int = 0,
                 configuration: UPowerConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or UPowerConfiguration()


class UPowerBatConfiguration:
    def __init__(self):
        pass


class UPowerBatSetup(ComponentSetup[UPowerBatConfiguration]):
    def __init__(self,
                 name: str = "UPower Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: UPowerBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or UPowerBatConfiguration())


class UPowerCounterConfiguration:
    def __init__(self):
        pass


class UPowerCounterSetup(ComponentSetup[UPowerCounterConfiguration]):
    def __init__(self,
                 name: str = "UPower Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: UPowerCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or UPowerCounterConfiguration())


class UPowerInverterConfiguration:
    def __init__(self):
        pass


class UPowerInverterSetup(ComponentSetup[UPowerInverterConfiguration]):
    def __init__(self,
                 name: str = "UPower Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: UPowerInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or UPowerInverterConfiguration())
