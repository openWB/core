from typing import Optional, List

from modules.common.component_setup import ComponentSetup


class JanitzaConfiguration:
    def __init__(self, modbus_id: int = 1, ip_address: Optional[str] = None, port: int = 502):
        self.modbus_id = modbus_id
        self.ip_address = ip_address
        self.port = port


class Janitza:
    def __init__(self,
                 name: str = "Janitza",
                 type: List[str] = ["janitza", "janitza"],
                 id: int = 0,
                 configuration: JanitzaConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.group = "other"
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
