#!/usr/bin/env python3
from typing import Optional

from helpermodules.auto_str import auto_str
from modules.devices.generic.json.config import (Json, JsonConfiguration, JsonCounterConfiguration,
                                                 JsonInverterConfiguration, JsonBatConfiguration,
                                                 JsonCounterSetup, JsonInverterSetup, JsonBatSetup)
from ..vendor import vendor_descriptor


@auto_str
class ZendureConfiguration(JsonConfiguration):
    def __init__(self, url: Optional[str] = None):
        self.url = f"http://{url}/properties/report"


@auto_str
class Zendure(Json):
    def __init__(self,
                 name: str = "Zendure",
                 type: str = "zendure",
                 id: int = 0,
                 configuration: ZendureConfiguration = None) -> None:
        super().__init__(name, type, id, configuration)
        self.vendor = vendor_descriptor.configuration_factory().type


@auto_str
class ZendureCounterConfiguration:
    def __init__(self):
        pass


@auto_str
class ZendureCounterSetup(JsonCounterSetup):
    def __init__(self,
                 name: str = "Zendure Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: JsonCounterConfiguration = None) -> None:
        super().__init__(name, type, id, JsonCounterConfiguration(
            jq_power=".properties.gridInputPower"))


@auto_str
class ZendureInverterConfiguration:
    def __init__(self):
        pass


@auto_str
class ZendureInverterSetup(JsonInverterSetup):
    def __init__(self,
                 name: str = "Zendure Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: JsonInverterConfiguration = None) -> None:
        super().__init__(name, type, id, JsonInverterConfiguration(
            jq_power="- .properties.solarInputPower"))


@auto_str
class ZendureBatConfiguration:
    def __init__(self):
        pass


@auto_str
class ZendureBatSetup(JsonBatSetup):
    def __init__(self,
                 name: str = "Zendure Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: JsonBatConfiguration = None) -> None:
        super().__init__(name, type, id, JsonBatConfiguration(
            jq_power=".properties.outputPackPower - .properties.packInputPower",
            jq_soc=".properties.electricLevel"))
