from typing import Optional, Tuple

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class BoschK40RfConfiguration:
    def __init__(self, ip_address: Optional[str] = None, port: int = 9443, token: Optional[str] = None):
        self.ip_address = ip_address
        self.port = port
        self.token = token


@auto_str
class BoschK40Rf(ConsumerSetup[BoschK40RfConfiguration]):
    def __init__(self,
                 name: str = "Wärmepumpe (K 40 RF Gateway - Bosch/Buderus/IVT/Vulcano/Worcester)",
                 type: str = "bosch_k40rf",
                 id: int = 0,
                 configuration: Optional[BoschK40RfConfiguration] = None,
                 usage: Tuple[ConsumerUsage, ...] = (ConsumerUsage.METER_ONLY,),
                 **kwargs) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or BoschK40RfConfiguration(), usage=usage, **kwargs)
