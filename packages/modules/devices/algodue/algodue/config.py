from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor
from helpermodules.auto_str import auto_str


class AlgodueConfiguration:
    def __init__(self, modbus_id: int = 1, ip_address: Optional[str] = None, port: int = 502):
        self.modbus_id = modbus_id
        self.ip_address = ip_address
        self.port = port


class Algodue:
    def __init__(self,
                 name: str = "Algodue",
                 type: str = "algodue",
                 id: int = 0,
                 configuration: AlgodueConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or AlgodueConfiguration()


@auto_str
class AlgodueCounterConfiguration:
    def __init__(self):
        pass


@auto_str
class AlgodueCounterSetup(ComponentSetup[AlgodueCounterConfiguration]):
    def __init__(self,
                 name: str = "Algodue Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: AlgodueCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or AlgodueCounterConfiguration())


@auto_str
class AlgodueInverterConfiguration:
    def __init__(self):
        pass


@auto_str
class AlgodueInverterSetup(ComponentSetup[AlgodueInverterConfiguration]):
    def __init__(self,
                 name: str = "Algodue Wechselrichterzähler",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: AlgodueInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or AlgodueInverterConfiguration())


@auto_str
class AlgodueBatConfiguration:
    def __init__(self):
        pass


@auto_str
class AlgodueBatSetup(ComponentSetup[AlgodueBatConfiguration]):
    def __init__(self,
                 name: str = "Algodue Speicherzähler",
                 type: str = "bat",
                 id: int = 0,
                 configuration: AlgodueBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or AlgodueBatConfiguration())
