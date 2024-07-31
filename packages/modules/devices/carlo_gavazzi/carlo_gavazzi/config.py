from typing import Optional, List

from modules.common.component_setup import ComponentSetup


class CarloGavazziConfiguration:
    def __init__(self, modbus_id: int = 1, ip_address: Optional[str] = None, port: int = 502):
        self.modbus_id = modbus_id
        self.ip_address = ip_address
        self.port = port


class CarloGavazzi:
    def __init__(self,
                 name: str = "Carlo Gavazzi",
                 type: List[str] = ["carlo_gavazzi", "carlo_gavazzi"],
                 id: int = 0,
                 configuration: CarloGavazziConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.group = "other"
        self.id = id
        self.configuration = configuration or CarloGavazziConfiguration()


class CarloGavazziCounterConfiguration:
    def __init__(self):
        pass


class CarloGavazziCounterSetup(ComponentSetup[CarloGavazziCounterConfiguration]):
    def __init__(self,
                 name: str = "Carlo Gavazzi Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: CarloGavazziCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or CarloGavazziCounterConfiguration())
