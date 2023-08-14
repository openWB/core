from typing import Optional

from modules.common.component_setup import ComponentSetup


class SolarmaxConfiguration:
    def __init__(self, ip_address: Optional[str] = None):
        self.ip_address = ip_address


class Solarmax:
    def __init__(self,
                 name: str = "Solarmax",
                 type: str = "solarmax",
                 id: int = 0,
                 configuration: SolarmaxConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or SolarmaxConfiguration()


class SolarmaxBatConfiguration:
    def __init__(self, modbus_id: int = 1):
        self.modbus_id = modbus_id


class SolarmaxBatSetup(ComponentSetup[SolarmaxBatConfiguration]):
    def __init__(self,
                 name: str = "Solarmax MAX.STORAGE / MAX.STORAGE Ultimate Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: SolarmaxBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SolarmaxBatConfiguration())


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
