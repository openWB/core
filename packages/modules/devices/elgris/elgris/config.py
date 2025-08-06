from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class ElgrisConfiguration:
    def __init__(self, modbus_id: int = 1, ip_address: Optional[str] = None, port: int = 502):
        self.modbus_id = modbus_id
        self.ip_address = ip_address
        self.port = port


class Elgris:
    def __init__(self,
                 name: str = "Elgris",
                 type: str = "elgris",
                 id: int = 0,
                 configuration: ElgrisConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or ElgrisConfiguration()


class ElgrisBatConfiguration:
    def __init__(self):
        pass


class ElgrisBatSetup(ComponentSetup[ElgrisBatConfiguration]):
    def __init__(self,
                 name: str = "Elgris Smart Meter Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: ElgrisBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or ElgrisBatConfiguration())


class ElgrisCounterConfiguration:
    def __init__(self):
        pass


class ElgrisCounterSetup(ComponentSetup[ElgrisCounterConfiguration]):
    def __init__(self,
                 name: str = "Elgris Smart Meter",
                 type: str = "counter",
                 id: int = 0,
                 configuration: ElgrisCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or ElgrisCounterConfiguration())


class ElgrisInverterConfiguration:
    def __init__(self):
        pass


class ElgrisInverterSetup(ComponentSetup[ElgrisInverterConfiguration]):
    def __init__(self,
                 name: str = "Elgris Smart Meter Welchselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: ElgrisInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or ElgrisInverterConfiguration())
