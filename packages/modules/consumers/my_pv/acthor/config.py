from typing import Optional, Tuple

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class ActhorConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: int = 502,
                 modbus_id: int = 1,
                 model: str = "9s45",
                 max_power: int = 1000):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id
        self.model = model
        self.max_power = max_power


@auto_str
class Acthor(ConsumerSetup[ActhorConfiguration]):
    def __init__(self,
                 name: str = "my-PV Acthor oder Elwa2 Heizstab",
                 type: str = "acthor",
                 id: int = 0,
                 configuration: Optional[ActhorConfiguration] = None,
                 usage: Tuple[ConsumerUsage, ...] = (ConsumerUsage.SUSPENDABLE_TUNABLE,
                                                     ConsumerUsage.METER_ONLY),
                 **kwargs) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or ActhorConfiguration(), usage=usage, **kwargs)
