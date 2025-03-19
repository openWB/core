from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class FemsConfiguration:
    def __init__(self, ip_address: Optional[str] = None, password: Optional[str] = None):
        self.ip_address = ip_address
        self.password = password


class Fems:
    def __init__(self,
                 name: str = "openEMS, Fenecon FEMS, CENTURIO 10, Kaco Hy-Control",
                 type: str = "fems",
                 id: int = 0,
                 configuration: FemsConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or FemsConfiguration()


class FemsBatConfiguration:
    def __init__(self, num: int = 1):
        self.num = num


class FemsBatSetup(ComponentSetup[FemsBatConfiguration]):
    def __init__(self,
                 name: str = "openEMS, Fenecon FEMS, CENTURIO 10, Kaco Hy-Control Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: FemsBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or FemsBatConfiguration())


class FemsCounterConfiguration:
    def __init__(self):
        pass


class FemsCounterSetup(ComponentSetup[FemsCounterConfiguration]):
    def __init__(self,
                 name: str = "openEMS, Fenecon FEMS, CENTURIO 10, Kaco Hy-Control Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: FemsCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or FemsCounterConfiguration())


class FemsInverterConfiguration:
    def __init__(self):
        pass


class FemsInverterSetup(ComponentSetup[FemsInverterConfiguration]):
    def __init__(self,
                 name: str = "openEMS, Fenecon FEMS, CENTURIO 10, Kaco Hy-Control Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: FemsInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or FemsInverterConfiguration())
