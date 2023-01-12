from modules.common.component_setup import ComponentSetup


class TasmotaConfiguration:
    def __init__(self, url=None):
        self.url = url


class Tasmota:
    def __init__(self,
                 name: str = "Tasmota",
                 type: str = "tasmota",
                 id: int = 0,
                 configuration: TasmotaConfiguration = None) -> None:
        self.name = name
        self.type = type
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
