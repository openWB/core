from typing import Optional

from helpermodules.auto_str import auto_str
from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


@auto_str
class SolarWorldConfiguration:
    def __init__(self, ip_address: Optional[str] = None):
        self.ip_address = ip_address


@auto_str
class SolarWorld:
    def __init__(self,
                 name: str = "SolarWorld",
                 type: str = "solar_world",
                 id: int = 0,
                 configuration: SolarWorldConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or SolarWorldConfiguration()


@auto_str
class SolarWorldCounterConfiguration:
    def __init__(self):
        pass


@auto_str
class SolarWorldCounterSetup(ComponentSetup[SolarWorldCounterConfiguration]):
    def __init__(self,
                 name: str = "SolarWorld Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: SolarWorldCounterConfiguration = None,
                 **kwargs) -> None:
        super().__init__(name, type, id, configuration or SolarWorldCounterConfiguration(), **kwargs)


@auto_str
class SolarWorldInverterConfiguration:
    def __init__(self):
        pass


@auto_str
class SolarWorldInverterSetup(ComponentSetup[SolarWorldInverterConfiguration]):
    def __init__(self,
                 name: str = "SolarWorld Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: SolarWorldInverterConfiguration = None,
                 **kwargs) -> None:
        super().__init__(name, type, id, configuration or SolarWorldInverterConfiguration(), **kwargs)
