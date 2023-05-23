from typing import Optional


class SmartWBConfiguration:
    def __init__(self, ip_address: Optional[str] = None, timeout: int = 2):
        self.ip_address = ip_address
        self.timeout = timeout


class SmartWB:
    def __init__(self,
                 name: str = "smartWB / EVSE-Wifi (>= v1.x.x/v2.x.x)",
                 type: str = "smartwb",
                 id: int = 0,
                 configuration: SmartWBConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or SmartWBConfiguration()
