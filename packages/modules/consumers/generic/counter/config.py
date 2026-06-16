from typing import List

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class CounterConfiguration:
    def __init__(self):
        pass


@auto_str
class Counter(ConsumerSetup[CounterConfiguration]):
    def __init__(self,
                 name: str = "openWB-kompatibler Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: CounterConfiguration = None,
                 usage: List[ConsumerUsage] = [ConsumerUsage.METER_ONLY]) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or CounterConfiguration(), usage=usage)
