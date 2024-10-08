from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class ZCSConfiguration:
    def __init__(self, modbus_id: int = 1, ip_address: Optional[str] = None, port: int = 502):
        self.modbus_id = modbus_id
        self.ip_address = ip_address
        self.port = port


class ZCS:
    def __init__(self,
                 name: str = "Azzurro - ZCS/Sofar HYD3-6k 1P",
                 type: str = "azzurro_zcs",
                 id: int = 0,
                 configuration: ZCSConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or ZCSConfiguration()


class ZCSBatConfiguration:
    def __init__(self):
        pass


class ZCSBatSetup(ComponentSetup[ZCSBatConfiguration]):
    def __init__(self,
                 name: str = "ZCS Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: ZCSBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or ZCSBatConfiguration())


class ZCSCounterConfiguration:
    def __init__(self):
        pass


class ZCSCounterSetup(ComponentSetup[ZCSCounterConfiguration]):
    def __init__(self,
                 name: str = "ZCS Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: ZCSCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or ZCSCounterConfiguration())


class ZCSInverterConfiguration:
    def __init__(self):
        pass


class ZCSInverterSetup(ComponentSetup[ZCSInverterConfiguration]):
    def __init__(self,
                 name: str = "ZCS Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: ZCSInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or ZCSInverterConfiguration())
