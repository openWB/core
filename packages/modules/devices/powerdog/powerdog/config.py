from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class PowerdogConfiguration:
    def __init__(self, modbus_id: int = 1, ip_address: Optional[str] = None, port: int = 502):
        self.modbus_id = modbus_id
        self.ip_address = ip_address
        self.port = port


class Powerdog:
    def __init__(self,
                 name: str = "Powerdog",
                 type: str = "powerdog",
                 id: int = 0,
                 configuration: PowerdogConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or PowerdogConfiguration()


class PowerdogCounterConfiguration:
    def __init__(self, position_evu: bool = False):
        self.position_evu = position_evu


class PowerdogCounterSetup(ComponentSetup[PowerdogCounterConfiguration]):
    def __init__(self,
                 name: str = "Powerdog Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: PowerdogCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or PowerdogCounterConfiguration())


class PowerdogInverterConfiguration:
    def __init__(self):
        pass


class PowerdogInverterSetup(ComponentSetup[PowerdogInverterConfiguration]):
    def __init__(self,
                 name: str = "Powerdog Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: PowerdogInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or PowerdogInverterConfiguration())
