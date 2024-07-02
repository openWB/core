from modules.common.component_setup import ComponentSetup
from typing import Optional


class TasmotaConfiguration:
    def __init__(self, ip_address: Optional[str] = None, phase: int = 1):
        self.ip_address = ip_address
        self.phase = phase


class Tasmota:
    def __init__(self,
                 name: str = "Tasmota",
                 type: str = "tasmota",
                 group: str = "other",
                 device: str = "Energiezähler",
                 id: int = 0,
                 configuration: TasmotaConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.group = group
        self.device = device
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
