from typing import Optional
from helpermodules.auto_str import auto_str
from modules.common.component_setup import ComponentSetup


@auto_str
class SampleConfiguration:
    def __init__(self, ip_address: Optional[str] = None):
        self.ip_address = ip_address


@auto_str
class Sample:
    def __init__(self,
                 name: str = "Sample",
                 type: str = "sample",
                 id: int = 0,
                 configuration: SampleConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or SampleConfiguration()


@auto_str
class SampleBatConfiguration:
    def __init__(self):
        pass


@auto_str
class SampleBatSetup(ComponentSetup[SampleBatConfiguration]):
    def __init__(self,
                 name: str = "Sample Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: SampleBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SampleBatConfiguration())


@auto_str
class SampleCounterConfiguration:
    def __init__(self):
        pass


@auto_str
class SampleCounterSetup(ComponentSetup[SampleCounterConfiguration]):
    def __init__(self,
                 name: str = "Sample Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: SampleCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SampleCounterConfiguration())


@auto_str
class SampleInverterConfiguration:
    def __init__(self):
        pass


@auto_str
class SampleInverterSetup(ComponentSetup[SampleInverterConfiguration]):
    def __init__(self,
                 name: str = "Sample Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: SampleInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SampleInverterConfiguration())
