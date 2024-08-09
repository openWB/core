#!/usr/bin/env python3
from typing import Optional

from helpermodules.auto_str import auto_str
from modules.devices.generic.json.config import Json, JsonConfiguration, JsonInverterConfiguration, JsonInverterSetup
from ..vendor import vendor_descriptor


@auto_str
class OpenDTUConfiguration(JsonConfiguration):
    def __init__(self, url: Optional[str] = None):
        self.url = "http://" + url + "/api/livedata/status"


@auto_str
class OpenDTU(Json):
    def __init__(self,
                 name: str = "Hoymiles über openDTU",
                 type: str = "opendtu",
                 id: int = 0,
                 configuration: OpenDTUConfiguration = None) -> None:
        super().__init__(name, type, id, configuration)
        self.vendor = vendor_descriptor.configuration_factory().type


@auto_str
class OpenDTUInverterConfiguration:
    def __init__(self):
        pass


@auto_str
class OpenDTUInverterSetup(JsonInverterSetup):
    def __init__(self,
                 name: str = "Hoymiles Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: JsonInverterConfiguration = None) -> None:
        super().__init__(name, type, id, JsonInverterConfiguration(
            jq_power=".total.Power.v", jq_exported=".total.YieldTotal.v*1000"))
