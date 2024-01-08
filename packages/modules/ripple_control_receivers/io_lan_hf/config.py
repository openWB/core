from typing import Optional


class IoLanRcrConfiguration:
    def __init__(self, ip_address: Optional[str] = None, port: int = 8899, modbus_id: int = 1):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id


class IoLanRcr:
    def __init__(self,
                 name: str = "IO-LAN-Modul HF6208, HF6508",
                 type: str = "io_lan_hf",
                 configuration: IoLanRcrConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or IoLanRcrConfiguration()
