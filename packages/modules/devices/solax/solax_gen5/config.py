from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class SolaxGen5Configuration:
    def __init__(self, modbus_id: int = 1, ip_address: Optional[str] = None, port: int = 502):
        self.modbus_id = modbus_id
        self.ip_address = ip_address
        self.port = port


class SolaxGen5:
    def __init__(self,
                 name: str = "Solax Gen5",
                 type: str = "solax_gen5",
                 id: int = 0,
                 configuration: SolaxGen5Configuration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or SolaxGen5Configuration()


class SolaxGen5BatConfiguration:
    def __init__(self):
        pass


class SolaxGen5BatSetup(ComponentSetup[SolaxGen5BatConfiguration]):
    def __init__(self,
                 name: str = "Solax Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: SolaxGen5BatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SolaxGen5BatConfiguration())


class SolaxGen5CounterConfiguration:
    def __init__(self):
        pass


class SolaxGen5CounterSetup(ComponentSetup[SolaxGen5CounterConfiguration]):
    def __init__(self,
                 name: str = "Solax Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: SolaxGen5CounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SolaxGen5CounterConfiguration())


class SolaxGen5InverterConfiguration:
    def __init__(self):
        pass


class SolaxGen5InverterSetup(ComponentSetup[SolaxGen5InverterConfiguration]):
    def __init__(self,
                 name: str = "Solax Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: SolaxGen5InverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SolaxGen5InverterConfiguration())
