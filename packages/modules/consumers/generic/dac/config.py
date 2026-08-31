from typing import Optional, Tuple

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from modules.consumers.generic.dac.model import Model
from ..vendor import vendor_descriptor


@auto_str
class DacConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: int = 502,
                 modbus_id: int = 1,
                 model: str = Model.N4Dac02.name,
                 full_signal_range: bool = False) -> None:
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id
        self.model = model
        self.full_signal_range = full_signal_range


@auto_str
class Dac(ConsumerSetup[DacConfiguration]):
    def __init__(self,
                 name: str = "Digital-Analog-Wandler (DAC)",
                 type: str = "dac",
                 id: int = 0,
                 configuration: Optional[DacConfiguration] = None,
                 usage: Tuple[ConsumerUsage, ...] = (ConsumerUsage.SUSPENDABLE_TUNABLE,),
                 **kwargs) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or DacConfiguration(), usage=usage, **kwargs)
