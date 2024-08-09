from typing import Optional

from helpermodules.auto_str import auto_str
from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class MTecConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: int = 502):
        self.ip_address = ip_address
        self.port = port


class MTec:
    def __init__(self,
                 name: str = "M-Tec",
                 type: str = "mtec",
                 id: int = 0,
                 configuration: MTecConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or MTecConfiguration()


@auto_str
class MTecBatConfiguration:
    def __init__(self, modbus_id: int = 247, generation: int = 2):
        self.modbus_id = modbus_id
        self.generation = generation


@auto_str
class MTecBatSetup(ComponentSetup[MTecBatConfiguration]):
    def __init__(self,
                 name: str = "M-Tec Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: MTecBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or MTecBatConfiguration())


@auto_str
class MTecCounterConfiguration:
    def __init__(self, modbus_id: int = 247):
        self.modbus_id = modbus_id


@auto_str
class MTecCounterSetup(ComponentSetup[MTecCounterConfiguration]):
    def __init__(self,
                 name: str = "M-Tec Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: MTecCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or MTecCounterConfiguration())


@auto_str
class MTecInverterConfiguration:
    def __init__(self, modbus_id: int = 247):
        self.modbus_id = modbus_id


@auto_str
class MTecInverterSetup(ComponentSetup[MTecInverterConfiguration]):
    def __init__(self,
                 name: str = "M-Tec Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: MTecInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or MTecInverterConfiguration())
