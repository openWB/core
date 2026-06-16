from typing import List

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class JsonConfiguration:
    def __init__(self,
                 url: str = None,
                 jq_current_l1: str = None,
                 jq_current_l2: str = None,
                 jq_current_l3: str = None,
                 jq_power: str = None,
                 jq_temperatures: str = None,
                 jq_imported: str = None,
                 jq_exported: str = None,
                 jq_switch_on: str = None,
                 jq_switch_off: str = None,
                 jq_set_power_limit: str = None):
        self.url = url
        self.jq_current_l1 = jq_current_l1
        self.jq_current_l2 = jq_current_l2
        self.jq_current_l3 = jq_current_l3
        self.jq_power = jq_power
        self.jq_temperatures = jq_temperatures
        self.jq_imported = jq_imported
        self.jq_exported = jq_exported
        self.jq_switch_on = jq_switch_on
        self.jq_switch_off = jq_switch_off
        self.jq_set_power_limit = jq_set_power_limit


@auto_str
class Json(ConsumerSetup[JsonConfiguration]):
    def __init__(self,
                 name: str = "JSON",
                 type: str = "json",
                 id: int = 0,
                 configuration: JsonConfiguration = None,
                 usage: List[ConsumerUsage] = [ConsumerUsage.METER_ONLY]) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or JsonConfiguration(), usage=usage)
