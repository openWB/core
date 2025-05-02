from typing import Optional
from helpermodules.auto_str import auto_str
from modules.common.component_setup import ComponentSetup


@auto_str
class MystromConfiguration:
    def __init__(self, ip_address: Optional[str] = None):
        self.ip_address = ip_address


@auto_str
class Mystrom:
    def __init__(self,
                 name: str = "mystrom",
                 type: str = "mystrom",
                 id: int = 0,
                 configuration: MystromConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or MystromConfiguration()


@auto_str
class MystromCounterConfiguration:
    def __init__(self):
        pass


@auto_str
class MystromCounterSetup(ComponentSetup[MystromCounterConfiguration]):
    def __init__(self,
                 name: str = "mystrom Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: MystromCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or MystromCounterConfiguration())
