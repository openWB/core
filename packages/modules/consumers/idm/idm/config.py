from typing import List, Optional

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class IdmConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: Optional[int] = 502,
                 modbus_id: Optional[int] = 1,
                 send_import: bool = False,
                 version: int = 1):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id
        self.send_import = send_import
        self.version = version


@auto_str
class Idm(ConsumerSetup[IdmConfiguration]):
    def __init__(self,
                 name: str = "Wärmepumpe der Firma IDM mit Navigatorregelung 1.7/2.0",
                 type: str = "idm",
                 id: int = 0,
                 configuration: IdmConfiguration = None,
                 usage: List[ConsumerUsage] = [ConsumerUsage.SUSPENDABLE_TUNABLE,
                                               ConsumerUsage.SUSPENDABLE_TUNABLE_INDIVIDUAL,
                                               ConsumerUsage.METER_ONLY]) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or IdmConfiguration(), usage=usage)
