from typing import Optional, Tuple

from control.consumer.usage import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class WallSocketConfiguration:
    def __init__(self, chargepoint_id: Optional[int] = None):
        self.chargepoint_id = chargepoint_id


@auto_str
class WallSocket(ConsumerSetup[WallSocketConfiguration]):
    def __init__(self, name: str = "Lokale Steckdose (SDM120)",
                 type: str = "gpio_sdm120",
                 id: int = 0,
                 configuration: Optional[WallSocketConfiguration] = None,
                 usage: Tuple[ConsumerUsage, ...] = (ConsumerUsage.SUSPENDABLE_ONOFF,
                                                     ConsumerUsage.METER_ONLY), **kwargs):
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory().type,
                         configuration=configuration or WallSocketConfiguration(), usage=usage, **kwargs)
