from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class JsonConfiguration:
    def __init__(self, url=None):
        self.url = url


class Json:
    def __init__(self,
                 name: str = "Json",
                 type: str = "json",
                 id: int = 0,
                 configuration: JsonConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or JsonConfiguration()


class JsonBatConfiguration:
    def __init__(self,
                 jq_imported: Optional[str] = None,
                 jq_exported: Optional[str] = None,
                 jq_soc: str = "",
                 jq_power: str = ""):
        self.jq_imported = jq_imported
        self.jq_exported = jq_exported
        self.jq_soc = jq_soc
        self.jq_power = jq_power


class JsonBatSetup(ComponentSetup[JsonBatConfiguration]):
    def __init__(self,
                 name: str = "Json Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: JsonBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or JsonBatConfiguration())


class JsonCounterConfiguration:
    def __init__(self, jq_power: str = "", jq_exported: Optional[str] = None, jq_imported: Optional[str] = None,
                 jq_power_l1: Optional[str] = None,
                 jq_power_l2: Optional[str] = None,
                 jq_power_l3: Optional[str] = None,
                 jq_current_l1: Optional[str] = None,
                 jq_current_l2: Optional[str] = None,
                 jq_current_l3: Optional[str] = None):
        self.jq_power = jq_power
        self.jq_exported = jq_exported
        self.jq_imported = jq_imported
        self.jq_powers = (jq_power_l1, jq_power_l2, jq_power_l3)
        self.jq_currents = (jq_current_l1, jq_current_l2, jq_current_l3)


class JsonCounterSetup(ComponentSetup[JsonCounterConfiguration]):
    def __init__(self,
                 name: str = "Json Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: JsonCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or JsonCounterConfiguration())


class JsonInverterConfiguration:
    def __init__(self, jq_power: str = "", jq_exported: Optional[str] = None):
        self.jq_power = jq_power
        self.jq_exported = jq_exported


class JsonInverterSetup(ComponentSetup[JsonInverterConfiguration]):
    def __init__(self,
                 name: str = "Json Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: JsonInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or JsonInverterConfiguration())
