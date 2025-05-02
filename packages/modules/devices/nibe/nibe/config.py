from typing import Optional
from helpermodules.auto_str import auto_str
from modules.common.component_setup import ComponentSetup


@auto_str
class NibeConfiguration:
    def __init__(self, ip_address: Optional[str] = None, port: int = 502):
        self.ip_address = ip_address
        self.port = port


@auto_str
class Nibe:
    def __init__(self,
                 name: str = "Nibe S-Series",
                 type: str = "nibe",
                 id: int = 0,
                 configuration: NibeConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or NibeConfiguration()


@auto_str
class NibeCounterConfiguration:
    def __init__(self, modbus_id: int = 1):
        self.modbus_id = modbus_id


@auto_str
class NibeCounterSetup(ComponentSetup[NibeCounterConfiguration]):
    def __init__(self,
                 name: str = "Nibe Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: NibeCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or NibeCounterConfiguration())
