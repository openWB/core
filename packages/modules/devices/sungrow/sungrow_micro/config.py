from typing import Optional

from modules.common.component_setup import ComponentSetup
from modules.devices.sungrow.sungrow_micro.version import Version
from ..vendor import vendor_descriptor


class SungrowMicroConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: int = 502,
                 modbus_id: int = 1):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id


class SungrowMicro:
    def __init__(self,
                 name: str = "Sungrow Microwechselrichter",
                 type: str = "sungrow_micro",
                 id: int = 0,
                 configuration: SungrowMicroConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or SungrowMicroConfiguration()


class SungrowMicroInverterConfiguration:
    def __init__(self):
        pass


class SungrowMicroInverterSetup(ComponentSetup[SungrowMicroInverterConfiguration]):
    def __init__(self,
                 name: str = "Sungrow Microwechselrichter SxxxxS",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: SungrowMicroInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SungrowMicroInverterConfiguration())
