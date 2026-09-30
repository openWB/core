from typing import Optional, Tuple

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class EgoConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: int = 502,
                 modbus_id: int = 247):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id


@auto_str
class Ego(ConsumerSetup[EgoConfiguration]):
    def __init__(self,
                 name: str = "E.G.O. Smart Heater",
                 type: str = "ego",
                 id: int = 0,
                 configuration: Optional[EgoConfiguration] = None,
                 usage: Tuple[ConsumerUsage, ...] = (ConsumerUsage.SUSPENDABLE_TUNABLE,
                                                     ConsumerUsage.SELF_CONTROLLED,
                                                     ConsumerUsage.METER_ONLY),
                 **kwargs) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or EgoConfiguration(), usage=usage, **kwargs)
