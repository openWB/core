from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class SofarConfiguration:
    def __init__(self, modbus_id: int = 1, ip_address: Optional[str] = None, port: int = 502):
        self.modbus_id = modbus_id
        self.ip_address = ip_address
        self.port = port


class Sofar:
    def __init__(self,
                 name: str = "SofarSolar",
                 type: str = "sofar",
                 id: int = 0,
                 configuration: SofarConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or SofarConfiguration()


class SofarBatConfiguration:
    def __init__(self):
        pass


class SofarBatSetup(ComponentSetup[SofarBatConfiguration]):
    def __init__(self,
                 name: str = "Sofar Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: SofarBatConfiguration = None,
                 **kwargs) -> None:
        super().__init__(name, type, id, configuration or SofarBatConfiguration(), **kwargs)


class SofarCounterConfiguration:
    def __init__(self):
        pass


class SofarCounterSetup(ComponentSetup[SofarCounterConfiguration]):
    def __init__(self,
                 name: str = "Sofar Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: SofarCounterConfiguration = None,
                 **kwargs) -> None:
        super().__init__(name, type, id, configuration or SofarCounterConfiguration(), **kwargs)


class SofarInverterConfiguration:
    def __init__(self):
        pass


class SofarInverterSetup(ComponentSetup[SofarInverterConfiguration]):
    def __init__(self,
                 name: str = "Sofar Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: SofarInverterConfiguration = None,
                 **kwargs) -> None:
        super().__init__(name, type, id, configuration or SofarInverterConfiguration(), **kwargs)
