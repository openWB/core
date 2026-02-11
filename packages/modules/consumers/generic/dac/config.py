from typing import List, Optional

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from modules.consumers.generic.dac.consumer import Model
from ..vendor import vendor_descriptor


@auto_str
class DacConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: Optional[int] = 502,
                 modbus_id: Optional[int] = 1,
                 model: Model = Model.N4Dac02.value,):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id
        self.model = model


@auto_str
class Dac(ConsumerSetup[DacConfiguration]):
    def __init__(self,
                 name: str = "Digital Analog Konverter (DAC) 0.01V bis 10.0V",
                 type: str = "dac",
                 id: int = 0,
                 configuration: DacConfiguration = None,
                 usage: List[ConsumerUsage] = [ConsumerUsage.SUSPENDABLE_TUNABLE,
                                               ConsumerUsage.SUSPENDABLE_TUNABLE_INDIVIDUAL]) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or DacConfiguration(), usage=usage)
