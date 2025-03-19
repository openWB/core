#!/usr/bin/env python3
from typing import Optional

from helpermodules.auto_str import auto_str
from modules.devices.generic.json.config import Json, JsonConfiguration, JsonInverterConfiguration, JsonInverterSetup
from ..vendor import vendor_descriptor


@auto_str
class BenningConfiguration(JsonConfiguration):
    def __init__(self, url: Optional[str] = None):
        self.url = "http://" + url + "/getentries.cgi?oids=11369,19000"


@auto_str
class Benning(Json):
    def __init__(self,
                 name: str = "Benning",
                 type: str = "benning",
                 id: int = 0,
                 configuration: BenningConfiguration = None) -> None:
        super().__init__(name, type, id, configuration)
        self.vendor = vendor_descriptor.configuration_factory().type


@auto_str
class BenningInverterConfiguration:
    def __init__(self):
        pass


@auto_str
class BenningInverterSetup(JsonInverterSetup):
    def __init__(self,
                 name: str = "Benning Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: JsonInverterConfiguration = None) -> None:
        super().__init__(name, type, id, JsonInverterConfiguration(
            jq_power=".[]|select(.oid==11365)|.val|tonumber", jq_exported=".[]|select(.oid==19000)|.val|tonumber"))
