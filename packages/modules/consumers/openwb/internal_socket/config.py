from typing import Optional, Tuple

from control.consumer.usage import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class InternalSocketConfiguration:
    def __init__(self, chargepoint_id: Optional[int] = None):
        self.chargepoint_id = chargepoint_id


@auto_str
class InternalSocket(ConsumerSetup[InternalSocketConfiguration]):
    def __init__(self, name: str = "Steckdose in openWB-Ladepunkt",
                 type: str = "internal_socket",
                 id: int = 0,
                 configuration: Optional[InternalSocketConfiguration] = None,
                 usage: Tuple[ConsumerUsage, ...] = (ConsumerUsage.SUSPENDABLE_ONOFF,
                                                     ConsumerUsage.CONTINUOUS,
                                                     ConsumerUsage.METER_ONLY), **kwargs):
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory().type,
                         configuration=configuration or InternalSocketConfiguration(), usage=usage, **kwargs)
