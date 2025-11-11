from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class SolarmaxConfiguration:
    def __init__(self, ip_address: Optional[str] = None, port: int = 502):
        self.ip_address = ip_address
        self.port = port


class Solarmax:
    def __init__(self,
                 name: str = "Solarmax",
                 type: str = "solarmax",
                 id: int = 0,
                 configuration: SolarmaxConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or SolarmaxConfiguration()


class SolarmaxMsCounterConfiguration:
    def __init__(self, modbus_id: int = 1):
        self.modbus_id = modbus_id


class SolarmaxMsCounterSetup(ComponentSetup[SolarmaxMsCounterConfiguration]):
    def __init__(self,
                 name: str = "Solarmax MAX.STORAGE / MAX.STORAGE Ultimate Zähler",
                 type: str = "counter_maxstorage",
                 id: Optional[int] = 0,
                 configuration: SolarmaxMsCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SolarmaxMsCounterConfiguration())


class SolarmaxBatConfiguration:
    def __init__(self, modbus_id: int = 1, power_limit_controllable: bool = False):
        self.modbus_id = modbus_id
        self.power_limit_controllable = power_limit_controllable


class SolarmaxBatSetup(ComponentSetup[SolarmaxBatConfiguration]):
    def __init__(self,
                 name: str = "Solarmax MAX.STORAGE / MAX.STORAGE Ultimate Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: SolarmaxBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SolarmaxBatConfiguration())


class SolarmaxMsInverterConfiguration:
    def __init__(self, modbus_id: int = 1):
        self.modbus_id = modbus_id


class SolarmaxMsInverterSetup(ComponentSetup[SolarmaxMsInverterConfiguration]):
    def __init__(self,
                 name: str = "Solarmax MAX.STORAGE / MAX.STORAGE Ultimate Wechselrichter",
                 type: str = "inverter_maxstorage",
                 id: int = 0,
                 configuration: SolarmaxMsInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SolarmaxMsInverterConfiguration())


class SolarmaxInverterConfiguration:
    def __init__(self, modbus_id: int = 1):
        self.modbus_id = modbus_id


class SolarmaxInverterSetup(ComponentSetup[SolarmaxInverterConfiguration]):
    def __init__(self,
                 name: str = "Solarmax Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: SolarmaxInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SolarmaxInverterConfiguration())
