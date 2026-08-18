from typing import Optional, Tuple

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class VampairConfiguration:
    def __init__(self, ip_address: Optional[str] = None, port: Optional[int] = 502, modbus_id: Optional[int] = 1):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id


@auto_str
class Vampair(ConsumerSetup[VampairConfiguration]):
    def __init__(self,
                 name: str = "Vampair Wärmepumpe",
                 type: str = "vampair",
                 id: int = 0,
                 configuration: VampairConfiguration = None,
                 usage: Tuple[ConsumerUsage, ...] = (ConsumerUsage.SELF_CONTROLLED,
                                                     ConsumerUsage.SUSPENDABLE_TUNABLE,
                                                     ConsumerUsage.METER_ONLY),
                 **kwargs) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or VampairConfiguration(), usage=usage, **kwargs)
