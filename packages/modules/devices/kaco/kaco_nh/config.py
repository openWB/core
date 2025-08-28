#!/usr/bin/env python3
from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class KacoNHConfiguration:
    def __init__(self, ip_address: Optional[str] = None, port: Optional[int] = None, serial: Optional[str] = None):
        self.ip_address = ip_address
        self.port = port
        self.serial = serial


class KacoNH:
    def __init__(self,
                 name: str = "KacoNH",
                 type: str = "kaco_nh",
                 id: int = 0,
                 configuration: KacoNHConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or KacoNHConfiguration()


class KacoNHBatConfiguration:
    def __init__(self, device_id: int = 0):
        self.device_id = device_id


class KacoNHBatSetup(ComponentSetup[KacoNHBatConfiguration]):
    def __init__(self,
                 name: str = "Kaco NH Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: KacoNHBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or KacoNHBatConfiguration())


class KacoNHCounterConfiguration:
    def __init__(self, device_id: int = 0):
        self.device_id = device_id


class KacoNHCounterSetup(ComponentSetup[KacoNHCounterConfiguration]):
    def __init__(self,
                 name: str = "Kaco NH Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: KacoNHCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or KacoNHCounterConfiguration())


class KacoNHInverterConfiguration:
    def __init__(self, device_id: int = 0):
        self.device_id = device_id


class KacoNHInverterSetup(ComponentSetup[KacoNHInverterConfiguration]):
    def __init__(self,
                 name: str = "KacoNH Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: KacoNHInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or KacoNHInverterConfiguration())
