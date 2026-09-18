from typing import Optional, Tuple

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class DaikinConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: int = 502,
                 modbus_id: int = 1):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id


@auto_str
class Daikin(ConsumerSetup[DaikinConfiguration]):
    def __init__(self,
                 name: str = "Daikin Altherma/Air2Air (HomeHub EKRHH)",
                 type: str = "daikin_homehub_air2air",
                 id: int = 0,
                 configuration: Optional[DaikinConfiguration] = None,
                 # Register gegen das offizielle EKRHH Installer Reference Guide (4PDE744838,
                 # Kap. 10 "Modbus TCP/IP oder RTU für Luft-zu-Luft-Wärmepumpe") geprüft.
                 usage: Tuple[ConsumerUsage, ...] = (ConsumerUsage.SUSPENDABLE_ONOFF,
                                                     ConsumerUsage.SUSPENDABLE_TUNABLE,
                                                     ConsumerUsage.METER_ONLY),
                 **kwargs) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or DaikinConfiguration(), usage=usage, **kwargs)
