from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class AnkerMeterConfiguration:
    def __init__(self, ip_address: Optional[str] = None, port: int = 502):
        self.ip_address = ip_address
        self.port = port


class AnkerMeter:
    def __init__(self,
                 name: str = "Anker SOLIX Smart Meter Gen 2",
                 type: str = "smartmeter_gen2",
                 id: int = 0,
                 configuration: AnkerMeterConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or AnkerMeterConfiguration()


class AnkerMeterCounterConfiguration:
    def __init__(self, modbus_id: int = 1):
        self.modbus_id = modbus_id


class AnkerMeterCounterSetup(ComponentSetup[AnkerMeterCounterConfiguration]):
    def __init__(self,
                 name: str = "Anker SOLIX Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: AnkerMeterCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or AnkerMeterCounterConfiguration())
