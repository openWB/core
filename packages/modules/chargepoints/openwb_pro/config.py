from typing import Optional


class OpenWBProConfiguration:
    def __init__(self, ip_address: Optional[str] = None, duo_num: int = 0):
        self.ip_address = ip_address
        self.duo_num = duo_num


class OpenWBPro:
    def __init__(self,
                 name: str = "openWB Pro",
                 type: str = "openwb_pro",
                 id: int = 0,
                 configuration: OpenWBProConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or OpenWBProConfiguration()
