from typing import Optional

from modules.common.component_setup import ComponentSetup
from modules.devices.good_we.good_we.version import GoodWeVersion
from ..vendor import vendor_descriptor


class GoodWeConfiguration:
    def __init__(self, ip_address: Optional[str] = None,
                 modbus_id: int = 247,
                 port: int = 502,
                 version: GoodWeVersion = GoodWeVersion.V_1_7,
                 firmware: int = 8):
        self.ip_address = ip_address
        self.modbus_id = modbus_id
        self.port = port
        self.version = version
        self.firmware = firmware


class GoodWe:
    def __init__(self,
                 name: str = "GoodWe ET-Serie",
                 type: str = "good_we",
                 id: int = 0,
                 configuration: GoodWeConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or GoodWeConfiguration()


class GoodWeBatConfiguration:
    def __init__(self):
        pass


class GoodWeBatSetup(ComponentSetup[GoodWeBatConfiguration]):
    def __init__(self,
                 name: str = "GoodWe Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: GoodWeBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or GoodWeBatConfiguration())


class GoodWeCounterConfiguration:
    def __init__(self):
        pass


class GoodWeCounterSetup(ComponentSetup[GoodWeCounterConfiguration]):
    def __init__(self,
                 name: str = "GoodWe Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: GoodWeCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or GoodWeCounterConfiguration())


class GoodWeInverterConfiguration:
    def __init__(self):
        pass


class GoodWeInverterSetup(ComponentSetup[GoodWeInverterConfiguration]):
    def __init__(self,
                 name: str = "GoodWe Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: GoodWeInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or GoodWeInverterConfiguration())
