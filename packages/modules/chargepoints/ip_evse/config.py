from typing import Optional


class IpEvseOpenWBConfiguration:
    def __init__(self, ip_address: Optional[str] = None, modbus_id: int = 1):
        self.ip_address = ip_address
        self.modbus_id = modbus_id


class IpEvseOpenWB:
    def __init__(self,
                 name: str = "openWB IP-EVSE",
                 type: str = "ip_evse",
                 id: int = 0,
                 configuration: IpEvseOpenWBConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or IpEvseOpenWBConfiguration()
