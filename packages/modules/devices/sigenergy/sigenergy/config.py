from typing import Optional
from helpermodules.auto_str import auto_str

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class SigenergyConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: int = 502):
        self.ip_address = ip_address
        self.port = port


class Sigenergy:
    def __init__(self,
                 name: str = "Sigenergy",
                 type: str = "sigenergy",
                 id: int = 0,
                 configuration: SigenergyConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or SigenergyConfiguration()


@auto_str
class SigenergyBatConfiguration:
    def __init__(self, modbus_id: int = 247):
        self.modbus_id = modbus_id


@auto_str
class SigenergyBatSetup(ComponentSetup[SigenergyBatConfiguration]):
    def __init__(self,
                 name: str = "Sigenergy Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: SigenergyBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SigenergyBatConfiguration())


@auto_str
class SigenergyCounterConfiguration:
    def __init__(self, modbus_id: int = 247):
        self.modbus_id = modbus_id


@auto_str
class SigenergyCounterSetup(ComponentSetup[SigenergyCounterConfiguration]):
    def __init__(self,
                 name: str = "Sigenergy Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: SigenergyCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SigenergyCounterConfiguration())


@auto_str
class SigenergyInverterConfiguration:
    def __init__(self, modbus_id: int = 247):
        self.modbus_id = modbus_id


@auto_str
class SigenergyInverterSetup(ComponentSetup[SigenergyInverterConfiguration]):
    def __init__(self,
                 name: str = "Sigenergy Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: SigenergyInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SigenergyInverterConfiguration())
