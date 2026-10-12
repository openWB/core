from typing import Optional, Tuple

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class DaikinAlthermaConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: int = 502,
                 modbus_id: int = 1):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id


@auto_str
class DaikinAltherma(ConsumerSetup[DaikinAlthermaConfiguration]):
    def __init__(self,
                 name: str = "Daikin Altherma (HomeHub)",
                 type: str = "daikin_homehub_altherma",
                 id: int = 0,
                 configuration: Optional[DaikinAlthermaConfiguration] = None,
                 # Register gegen das offizielle EKRHH Installer Reference Guide (4PDE744838,
                 # Kap. 9 "Modbus TCP/IP oder RTU für Daikin Altherma") geprüft.
                 usage: Tuple[ConsumerUsage, ...] = (ConsumerUsage.SUSPENDABLE_ONOFF,
                                                     ConsumerUsage.SUSPENDABLE_TUNABLE,
                                                     ConsumerUsage.METER_ONLY),
                 **kwargs) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or DaikinAlthermaConfiguration(), usage=usage, **kwargs)
