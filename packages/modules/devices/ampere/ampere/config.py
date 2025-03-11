from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class AmpereConfiguration:
    def __init__(self, modbus_id: int = 1, ip_address: Optional[str] = None, port: int = 502):
        self.modbus_id = modbus_id
        self.ip_address = ip_address
        self.port = port


class Ampere:
    def __init__(self,
                 name: str = "Ampere Pro",
                 type: str = "ampere",
                 id: int = 0,
                 configuration: AmpereConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or AmpereConfiguration()


class AmpereBatConfiguration:
    def __init__(self):
        pass


class AmpereBatSetup(ComponentSetup[AmpereBatConfiguration]):
    def __init__(self,
                 name: str = "Ampere Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: AmpereBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or AmpereBatConfiguration())


class AmpereCounterConfiguration:
    def __init__(self):
        pass


class AmpereCounterSetup(ComponentSetup[AmpereCounterConfiguration]):
    def __init__(self,
                 name: str = "Ampere Pro Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: AmpereCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or AmpereCounterConfiguration())


class AmpereInverterConfiguration:
    def __init__(self):
        pass


class AmpereInverterSetup(ComponentSetup[AmpereInverterConfiguration]):
    def __init__(self,
                 name: str = "Ampere Pro Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: AmpereInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or AmpereInverterConfiguration())
