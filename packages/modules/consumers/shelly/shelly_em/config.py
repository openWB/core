from typing import List, Optional

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class ShellyEMConfiguration:
    def __init__(self, ip_address: Optional[str] = None, username: Optional[str] = None,
                 password: Optional[str] = None, channel: int = 0, phase: int = 1, factor: float = 1.0) -> None:
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.channel = channel  # Channel 0: alle Meter summiert
        self.phase = phase
        self.factor = factor


@auto_str
class ShellyEM(ConsumerSetup[ShellyEMConfiguration]):
    def __init__(self,
                 name: str = "Shelly EM (Messen)",
                 type: str = "shelly_em",
                 id: int = 0,
                 configuration: ShellyEMConfiguration = None,
                 usage: List[ConsumerUsage] = [ConsumerUsage.METER_ONLY]) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or ShellyEMConfiguration(), usage=usage)
