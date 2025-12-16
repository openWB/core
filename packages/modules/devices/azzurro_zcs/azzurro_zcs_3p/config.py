from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class ZCS3PConfiguration:
    def __init__(self, modbus_id: int = 1, ip_address: Optional[str] = None, port: int = 502):
        self.modbus_id = modbus_id
        self.ip_address = ip_address
        self.port = port


class ZCS3P:
    def __init__(self,
                 name: str = "Azzurro - ZCS 3PH 12KTL",
                 type: str = "azzurro_zcs_3p",
                 id: int = 0,
                 configuration: ZCS3PConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or ZCS3PConfiguration()


class ZCSPvInverterConfiguration:
    def __init__(self):
        pass


class ZCSPvInverterSetup(ComponentSetup[ZCSPvInverterConfiguration]):
    def __init__(self,
                 name: str = "ZCS Azzurro Wechselrichter",
                 type: str = "pv_inverter",
                 id: int = 0,
                 configuration: ZCSPvInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or ZCSPvInverterConfiguration())
