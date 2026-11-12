#!/usr/bin/env python3
from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class SunspecConfiguration:
    def __init__(self, ip_address: Optional[str] = None, port: int = 502) -> None:
        self.ip_address = ip_address
        self.port = port


class Sunspec:
    def __init__(self,
                 name: str = "SunSpec",
                 type: str = "sunspec",
                 id: int = 0,
                 configuration: SunspecConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or SunspecConfiguration()


class SunspecCounterConfiguration:
    def __init__(self, modbus_id: int = 1) -> None:
        self.modbus_id = modbus_id


class SunspecCounterSetup(ComponentSetup[SunspecCounterConfiguration]):
    def __init__(self,
                 name: str = "SunSpec Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: SunspecCounterConfiguration = None,
                 **kwargs) -> None:
        super().__init__(name, type, id, configuration or SunspecCounterConfiguration(), **kwargs)


class SunspecInverterConfiguration:
    def __init__(self, modbus_id: int = 1) -> None:
        self.modbus_id = modbus_id


class SunspecInverterSetup(ComponentSetup[SunspecInverterConfiguration]):
    def __init__(self,
                 name: str = "SunSpec Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: SunspecInverterConfiguration = None,
                 **kwargs) -> None:
        super().__init__(name, type, id, configuration or SunspecInverterConfiguration(), **kwargs)


class SunspecBatConfiguration:
    def __init__(self, modbus_id: int = 1) -> None:
        self.modbus_id = modbus_id


class SunspecBatSetup(ComponentSetup[SunspecBatConfiguration]):
    def __init__(self,
                 name: str = "SunSpec Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: SunspecBatConfiguration = None,
                 **kwargs) -> None:
        super().__init__(name, type, id, configuration or SunspecBatConfiguration(), **kwargs)
