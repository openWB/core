from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class SiemensLogo84Configuration:
    def __init__(self, modbus_id: int = 1, ip_address: Optional[str] = None, port: int = 507):
        self.modbus_id = modbus_id
        self.ip_address = ip_address
        self.port = port


class SiemensLogo84:
    def __init__(self,
                 name: str = "Siemens LOGO!8.4",
                 type: str = "siemens_logo84",
                 id: int = 0,
                 configuration: SiemensLogo84Configuration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or SiemensLogo84Configuration()


class SiemensLogo84BatConfiguration:
    def __init__(self):
        pass


class SiemensLogo84BatSetup(ComponentSetup[SiemensLogo84BatConfiguration]):
    def __init__(self,
                 name: str = "Siemens LOGO! 8.4 Speicher-Zähler",
                 type: str = "bat",
                 id: int = 0,
                 configuration: SiemensLogo84BatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SiemensLogo84BatConfiguration())
