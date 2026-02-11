from typing import List, Optional

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class StiebelConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: Optional[int] = 502,
                 modbus_id: Optional[int] = 1):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id


@auto_str
class Stiebel(ConsumerSetup[StiebelConfiguration]):
    def __init__(self,
                 name: str = "Stiebel",
                 type: str = "stiebel",
                 id: int = 0,
                 configuration: StiebelConfiguration = None,
                 usage: List[ConsumerUsage] = [ConsumerUsage.SUSPENDABLE_ONOFF,
                                               ConsumerUsage.SUSPENDABLE_ONOFF_INDIVIDUAL]) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or StiebelConfiguration(), usage=usage)
