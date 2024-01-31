from typing import Optional


class IoLanRcrConfiguration:
    def __init__(self, ip_address: Optional[str] = None, port: int = 8899, modbus_id: int = 1):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id


class IoLanRcr:
    def __init__(self,
                 name: str = "Dimm-Kit",
                 type: str = "dimm_kit",
                 configuration: IoLanRcrConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or IoLanRcrConfiguration()
