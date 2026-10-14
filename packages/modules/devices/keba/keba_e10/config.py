from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class KebaE10Configuration:
    def __init__(self, ip_address: Optional[str] = None, port: int = 502, modbus_id: int = 1):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id


class KebaE10:
    def __init__(self, name: str = "KEBA KeContact E10", type: str = "keba_e10",
                 id: int = 0, configuration: KebaE10Configuration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or KebaE10Configuration()


class KebaE10CounterConfiguration:
    def __init__(self) -> None:
        pass


class KebaE10CounterSetup(ComponentSetup[KebaE10CounterConfiguration]):
    def __init__(self, name: str = "KEBA KeContact E10 EVU-Zähler", type: str = "counter",
                 id: int = 0, configuration: KebaE10CounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or KebaE10CounterConfiguration())

        self.info["manufacturer"] = "KEBA"
        self.info["model"] = "Keba KeContact E10 Smart Energy Meter"
