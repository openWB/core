from enum import Enum


class InternalChargepointMode(Enum):
    SOCKET = "socket"
    DUO = "duo"
    SERIES = "series"


class InternalOpenWBConfiguration:
    def __init__(self, mode: str = InternalChargepointMode.SERIES.value, duo_num: int = 0):
        self.mode = mode
        self.ip_address = "localhost"
        self.duo_num = duo_num


class InternalOpenWB:
    def __init__(self,
                 name: str = "Interne openWB",
                 type: str = "internal_openwb",
                 id: int = 0,
                 configuration: InternalOpenWBConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or InternalOpenWBConfiguration()
