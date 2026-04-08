from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class SungrowSGConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: int = 502,
                 modbus_id: int = 1):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id


class SungrowSG:
    def __init__(self,
                 name: str = "Sungrow SG",
                 type: str = "sungrow_sg",
                 id: int = 0,
                 configuration: SungrowSGConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or SungrowSGConfiguration()


class SungrowSGCounterConfiguration:
    def __init__(self):
        pass


class SungrowSGCounterSetup(ComponentSetup[SungrowSGCounterConfiguration]):
    def __init__(self,
                 name: str = "Sungrow SG Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: SungrowSGCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SungrowSGCounterConfiguration())


class SungrowSGInverterConfiguration:
    def __init__(self):
        pass


class SungrowSGInverterSetup(ComponentSetup[SungrowSGInverterConfiguration]):
    def __init__(self,
                 name: str = "Sungrow SG Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: SungrowSGInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SungrowSGInverterConfiguration())
