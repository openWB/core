from typing import List, Optional

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class AvmConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 session_id: Optional[str] = None,
                 session_mtime: Optional[str] = None,
                 name: Optional[str] = None) -> None:
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.session_id = session_id  # don't show in UI
        self.session_mtime = session_mtime  # don't show in UI
        self.name = name


@auto_str
class Avm(ConsumerSetup[AvmConfiguration]):
    def __init__(self,
                 name: str = "AVM Fritz!Box",
                 type: str = "avm",
                 id: int = 0,
                 configuration: AvmConfiguration = None,
                 usage: List[ConsumerUsage] = [ConsumerUsage.SUSPENDABLE_TUNABLE,
                                               ConsumerUsage.SUSPENDABLE_TUNABLE_INDIVIDUAL,
                                               ConsumerUsage.METER_ONLY]) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or AvmConfiguration(), usage=usage)
