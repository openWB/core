from typing import List, Optional

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class MyStromConfiguration:
    def __init__(self, ip_address: Optional[str] = None):
        self.ip_address = ip_address


@auto_str
class MyStrom(ConsumerSetup[MyStromConfiguration]):
    def __init__(self,
                 name: str = "MyStrom",
                 type: str = "mystrom",
                 id: int = 0,
                 configuration: MyStromConfiguration = None,
                 usage: List[ConsumerUsage] = [ConsumerUsage.SUSPENDABLE_ONOFF,
                                               ConsumerUsage.SUSPENDABLE_ONOFF_INDIVIDUAL,
                                               ConsumerUsage.METER_ONLY]) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or MyStromConfiguration(), usage=usage)
