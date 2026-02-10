from typing import List, Optional

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class ActhorConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: Optional[int] = 502,
                 modbus_id: Optional[int] = 1,
                 model: Optional[str] = "9s45",
                 max_power: Optional[int] = 1000):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id
        self.model = model
        self.max_power = max_power


@auto_str
class Acthor(ConsumerSetup[ActhorConfiguration]):
    def __init__(self,
                 name: str = "my-PV Acthor",
                 type: str = "acthor",
                 id: int = 0,
                 configuration: ActhorConfiguration = None,
                 usage: List[ConsumerUsage] = [ConsumerUsage.SUSPENDABLE_TUNABLE,
                                               ConsumerUsage.SUSPENDABLE_TUNABLE_INDIVIDUAL,
                                               ConsumerUsage.METER_ONLY]) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or ActhorConfiguration(), usage=usage)
