from enum import Enum
from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class EnphaseVersion(Enum):
    V1 = 1
    V2 = 2


class EnphaseConfiguration:
    def __init__(self, hostname: Optional[str] = None,
                 version: EnphaseVersion = EnphaseVersion.V1,
                 user: Optional[str] = None,
                 password: Optional[str] = None,
                 serial: Optional[str] = None,
                 token: Optional[str] = None):
        self.hostname = hostname
        self.version = version
        self.user = user
        self.password = password
        self.serial = serial
        self.token = token


class Enphase:
    def __init__(self,
                 name: str = "Enphase",
                 type: str = "enphase",
                 id: int = 0,
                 configuration: EnphaseConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or EnphaseConfiguration()


class EnphaseCounterConfiguration:
    def __init__(self, eid=None):
        self.eid = eid


class EnphaseCounterSetup(ComponentSetup[EnphaseCounterConfiguration]):
    def __init__(self,
                 name: str = "Enphase Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: EnphaseCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or EnphaseCounterConfiguration())


class EnphaseInverterConfiguration:
    def __init__(self, eid=None):
        self.eid = eid


class EnphaseInverterSetup(ComponentSetup[EnphaseInverterConfiguration]):
    def __init__(self,
                 name: str = "Enphase Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: EnphaseInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or EnphaseInverterConfiguration())


class EnphaseBatConfiguration:
    def __init__(self):
        pass


class EnphaseBatSetup(ComponentSetup[EnphaseBatConfiguration]):
    def __init__(self,
                 name: str = "Enphase Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: EnphaseBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or EnphaseBatConfiguration())
