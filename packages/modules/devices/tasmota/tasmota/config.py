from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class TasmotaConfiguration:
    def __init__(self, ip_address: Optional[str] = None, phase: int = 1):
        self.ip_address = ip_address
        self.phase = phase


class Tasmota:
    def __init__(self,
                 name: str = "Tasmota",
                 type: str = "tasmota",
                 id: int = 0,
                 configuration: TasmotaConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or TasmotaConfiguration()


class TasmotaCounterConfiguration:
    def __init__(self):
        pass


class TasmotaCounterSetup(ComponentSetup[TasmotaCounterConfiguration]):
    def __init__(self,
                 name: str = "Tasmota Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: TasmotaCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or TasmotaCounterConfiguration())


class TasmotaInverterConfiguration:
    def __init__(self):
        pass


class TasmotaInverterSetup(ComponentSetup[TasmotaInverterConfiguration]):
    def __init__(self,
                 name: str = "Tasmota Wechselrichterzähler",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: TasmotaInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or TasmotaInverterConfiguration())


class TasmotaBatConfiguration:
    def __init__(self):
        pass


class TasmotaBatSetup(ComponentSetup[TasmotaBatConfiguration]):
    def __init__(self,
                 name: str = "Tasmota Speicherzähler",
                 type: str = "bat",
                 id: int = 0,
                 configuration: TasmotaBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or TasmotaBatConfiguration())
