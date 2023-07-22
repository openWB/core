from typing import Optional


class OpenWBseries2SatellitConfiguration:
    def __init__(self, ip_address: Optional[str] = None, duo_num: int = 0):
        self.ip_address = ip_address
        self.duo_num = duo_num


class OpenWBseries2Satellit:
    def __init__(self,
                 name: str = "openWB series2 satellit, openWB series2 satellit Duo",
                 type: str = "openwb_series2_satellit",
                 id: int = 0,
                 configuration: OpenWBseries2SatellitConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or OpenWBseries2SatellitConfiguration()
