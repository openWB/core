from typing import Optional


class OpenWBseries2SatellitConfiguration:
    def __init__(self, ip_address: Optional[str] = None, counter_type: str = "sdm630"):
        self.ip_address = ip_address
        self.counter_type = counter_type


class OpenWBseries2Satellit:
    def __init__(self,
                 name: str = "openWB series2 satellit",
                 type: str = "openwb_series2_satellit",
                 id: int = 0,
                 configuration: OpenWBseries2SatellitConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or OpenWBseries2SatellitConfiguration()
