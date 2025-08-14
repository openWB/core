from typing import Optional

from helpermodules.auto_str import auto_str
from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class KostalPikoCiConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: int = 502):
        self.ip_address = ip_address
        self.port = port


class KostalPikoCi:
    def __init__(self,
                 name: str = "Kostal Piko CI",
                 type: str = "kostal_piko_ci",
                 id: int = 0,
                 configuration: KostalPikoCiConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or KostalPikoCiConfiguration()


@auto_str
class KostalPikoCiCounterConfiguration:
    def __init__(self, modbus_id: int = 247):
        self.modbus_id = modbus_id


@auto_str
class KostalPikoCiCounterSetup(ComponentSetup[KostalPikoCiCounterConfiguration]):
    def __init__(self,
                 name: str = "Kostal Piko CI Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: KostalPikoCiCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or KostalPikoCiCounterConfiguration())


@auto_str
class KostalPikoCiInverterConfiguration:
    def __init__(self, modbus_id: int = 247):
        self.modbus_id = modbus_id


@auto_str
class KostalPikoCiInverterSetup(ComponentSetup[KostalPikoCiInverterConfiguration]):
    def __init__(self,
                 name: str = "Kostal Piko CI Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: KostalPikoCiInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or KostalPikoCiInverterConfiguration())
