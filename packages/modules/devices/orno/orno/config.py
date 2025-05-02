from typing import Optional
from helpermodules.auto_str import auto_str
from modules.common.component_setup import ComponentSetup


@auto_str
class OrnoConfiguration:
    def __init__(self, ip_address: Optional[str] = None, port: int = 502) -> None:
        self.ip_address = ip_address
        self.port = port


@auto_str
class Orno:
    def __init__(self,
                 name: str = "Orno WE-514",
                 type: str = "orno",
                 id: int = 0,
                 configuration: OrnoConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or OrnoConfiguration()


@auto_str
class OrnoCounterConfiguration:
    def __init__(self, modbus_id: int = 1):
        self.modbus_id = modbus_id


@auto_str
class OrnoCounterSetup(ComponentSetup[OrnoCounterConfiguration]):
    def __init__(self,
                 name: str = "Orno Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: OrnoCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or OrnoCounterConfiguration())
