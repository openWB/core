from typing import Optional


class ExternalOpenWBConfiguration:
    def __init__(self, ip_address: Optional[str] = None, duo_num: int = 1):
        self.ip_address = ip_address
        self.duo_num = duo_num


class ExternalOpenWB:
    def __init__(self,
                 name: str = "Externe openWB",
                 type: str = "external_openwb",
                 id: int = 0,
                 configuration: ExternalOpenWBConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or ExternalOpenWBConfiguration()
