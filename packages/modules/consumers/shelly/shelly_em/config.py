from typing import List, Optional

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class ShellyConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 factor: Optional[int] = -1,
                 phase: Optional[int] = 1,
                 username: Optional[str] = None,
                 password: Optional[str] = None) -> None:
        self.ip_address = ip_address
        self.factor = factor
        self.phase = phase
        self.username = username
        self.password = password


@auto_str
class ShellyPM(ConsumerSetup[ShellyConfiguration]):
    def __init__(self,
                 name: str = "Shelly PM (Messen & Schalten)",
                 type: str = "shelly_pm",
                 id: int = 0,
                 configuration: ShellyConfiguration = None,
                 usage: List[ConsumerUsage] = [ConsumerUsage.METER_ONLY]) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or ShellyConfiguration(), usage=usage)
