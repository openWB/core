from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class KostalSemConfiguration:
    def __init__(self, modbus_id: int = 71, ip_address: Optional[str] = None, port: int = 502):
        self.modbus_id = modbus_id
        self.ip_address = ip_address
        self.port = port


class KostalSem:
    def __init__(self,
                 name: str = "Kostal Smart Energy Meter oder TQ EM 410",
                 type: str = "kostal_sem",
                 id: int = 0,
                 configuration: KostalSemConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or KostalSemConfiguration()


class KostalSemCounterConfiguration:
    def __init__(self):
        pass


class KostalSemCounterSetup(ComponentSetup[KostalSemCounterConfiguration]):
    def __init__(self,
                 name: str = "Kostal Smart Energy Meter oder TQ EM 410 Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: KostalSemCounterConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or KostalSemCounterConfiguration()
