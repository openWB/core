from typing import Optional, Tuple

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class GreeConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: int = 7000):
        self.ip_address = ip_address
        self.port = port


@auto_str
class Gree(ConsumerSetup[GreeConfiguration]):
    def __init__(self,
                 name: str = "Gree Klimaanlage",
                 type: str = "gree",
                 id: int = 0,
                 configuration: Optional[GreeConfiguration] = None,
                 # UNVERIFIZIERT: kein offizielles Gree-Protokoll veröffentlicht, community-seitig
                 # reverse-engineert (mehrere unabhängige Implementierungen stimmen überein).
                 usage: Tuple[ConsumerUsage, ...] = (ConsumerUsage.SUSPENDABLE_ONOFF,),
                 **kwargs) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or GreeConfiguration(), usage=usage, **kwargs)
