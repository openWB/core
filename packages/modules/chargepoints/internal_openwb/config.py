from enum import Enum

from modules.common.abstract_chargepoint import SetupChargepoint


class InternalChargepointMode(Enum):
    DUO = "duo"
    PRO_PLUS = "pro_plus"
    SERIES = "series"
    SOCKET = "socket"


class InternalOpenWBConfiguration:
    def __init__(self, mode: str = InternalChargepointMode.SERIES.value, duo_num: int = 0):
        self.mode = mode
        self.ip_address = "localhost"
        self.duo_num = duo_num


class InternalOpenWB(SetupChargepoint[InternalOpenWBConfiguration]):
    def __init__(self,
                 name: str = "Interne openWB",
                 type: str = "internal_openwb",
                 id: int = 0,
                 configuration: InternalOpenWBConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or InternalOpenWBConfiguration())
