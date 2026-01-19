from typing import List

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class MqttConfiguration:
    def __init__(self):
        pass


@auto_str
class Mqtt(ConsumerSetup[MqttConfiguration]):
    def __init__(self,
                 name: str = "Mqtt",
                 type: str = "mqtt",
                 id: int = 0,
                 configuration: MqttConfiguration = None,
                 usage: List[ConsumerUsage] = [ConsumerUsage.METER_ONLY,
                                               ConsumerUsage.CONTINUOUS,
                                               ConsumerUsage.SUSPENDABLE_ONOFF,
                                               ConsumerUsage.SUSPENDABLE_ONOFF_INDIVIDUAL,
                                               ConsumerUsage.SUSPENDABLE_TUNABLE,
                                               ConsumerUsage.SUSPENDABLE_TUNABLE_INDIVIDUAL]) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or MqttConfiguration(), usage=usage)
