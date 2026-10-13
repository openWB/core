from typing import Optional, Tuple

from control.consumer.usage import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class GpioSdm120Configuration:
    def __init__(self, chargepoint_id: Optional[int] = None):
        self.chargepoint_id = chargepoint_id


@auto_str
class GpioSdm120(ConsumerSetup[GpioSdm120Configuration]):
    def __init__(self, name: str = "Lokale Steckdose (SDM120)",
                 type: str = "gpio_sdm120",
                 id: int = 0,
                 configuration: Optional[GpioSdm120Configuration] = None,
                 usage: Tuple[ConsumerUsage, ...] = (ConsumerUsage.SUSPENDABLE_ONOFF,), **kwargs):
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory().type,
                         configuration=configuration or GpioSdm120Configuration(), usage=usage, **kwargs)
