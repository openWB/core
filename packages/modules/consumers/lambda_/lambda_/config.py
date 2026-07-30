from typing import Optional, Tuple

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class LambdaConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: Optional[int] = 502,
                 modbus_id: Optional[int] = 1,
                 send_values: bool = False):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id
        self.send_values = send_values


@auto_str
class Lambda(ConsumerSetup[LambdaConfiguration]):
    def __init__(self,
                 name: str = "Lambda Wärmepumpe",
                 type: str = "lambda",
                 id: int = 0,
                 configuration: LambdaConfiguration = None,
                 usage: Tuple[ConsumerUsage, ...] = (ConsumerUsage.SUSPENDABLE_TUNABLE,
                                                     ConsumerUsage.METER_ONLY),
                 **kwargs) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or LambdaConfiguration(), usage=usage, **kwargs)
