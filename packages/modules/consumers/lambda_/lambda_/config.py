from typing import Optional, Tuple

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class LambdaConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: int = 502,
                 modbus_id: int = 1):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id


@auto_str
class Lambda(ConsumerSetup[LambdaConfiguration]):
    def __init__(self,
                 name: str = "Lambda Wärmepumpe",
                 type: str = "lambda_",
                 id: int = 0,
                 configuration: Optional[LambdaConfiguration] = None,
                 usage: Tuple[ConsumerUsage, ...] = (ConsumerUsage.SUSPENDABLE_TUNABLE,
                                                     ConsumerUsage.SELF_CONTROLLED,
                                                     ConsumerUsage.METER_ONLY),
                 **kwargs) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or LambdaConfiguration(), usage=usage, **kwargs)
