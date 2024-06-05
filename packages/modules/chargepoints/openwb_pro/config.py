from typing import Optional

from modules.common.abstract_chargepoint import SetupChargepoint


class OpenWBProConfiguration:
    def __init__(self, ip_address: Optional[str] = None, duo_num: int = 0):
        self.ip_address = ip_address
        self.duo_num = duo_num


class OpenWBPro(SetupChargepoint[OpenWBProConfiguration]):
    def __init__(self,
                 name: str = "openWB Pro",
                 type: str = "openwb_pro",
                 id: int = 0,
                 configuration: OpenWBProConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or OpenWBProConfiguration())
