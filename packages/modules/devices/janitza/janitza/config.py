from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class JanitzaConfiguration:
    def __init__(self, modbus_id: int = 1, ip_address: Optional[str] = None, port: int = 502):
        self.modbus_id = modbus_id
        self.ip_address = ip_address
        self.port = port


class Janitza:
    def __init__(self,
                 name: str = "Janitza",
                 type: str = "janitza",
                 id: int = 0,
                 configuration: JanitzaConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or JanitzaConfiguration()


class JanitzaCounterConfiguration:
    def __init__(self):
        pass


class JanitzaCounterSetup(ComponentSetup[JanitzaCounterConfiguration]):
    def __init__(self,
                 name: str = "Janitza Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: JanitzaCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or JanitzaCounterConfiguration())
