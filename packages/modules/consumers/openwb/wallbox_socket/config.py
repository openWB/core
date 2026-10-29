from typing import Optional, Tuple

from control.consumer.usage import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class WallboxSocketConfiguration:
    def __init__(self, chargepoint_id: Optional[int] = None):
        self.chargepoint_id = chargepoint_id


@auto_str
class WallboxSocket(ConsumerSetup[WallboxSocketConfiguration]):
    def __init__(self, name: str = "Wallbox-Steckdose",
                 type: str = "wallbox_socket",
                 id: int = 0,
                 configuration: Optional[WallboxSocketConfiguration] = None,
                 usage: Tuple[ConsumerUsage, ...] = (ConsumerUsage.SUSPENDABLE_ONOFF,
                                                     ConsumerUsage.CONTINUOUS), **kwargs):
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory().type,
                         configuration=configuration or WallboxSocketConfiguration(), usage=usage, **kwargs)
