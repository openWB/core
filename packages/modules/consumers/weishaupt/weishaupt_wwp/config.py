from typing import Optional, Tuple

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class WeishauptConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: int = 502,
                 modbus_id: int = 1):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id


@auto_str
class Weishaupt(ConsumerSetup[WeishauptConfiguration]):
    def __init__(self,
                 name: str = "Weishaupt Wärmepumpe (AEROBLOCK/BIBLOCK/SPLITBLOCK/GEOBLOCK)",
                 type: str = "weishaupt_wwp",
                 id: int = 0,
                 configuration: Optional[WeishauptConfiguration] = None,
                 # kein SUSPENDABLE_ONOFF: die SG-Ready-Eingänge sind auf diesen Geräten laut
                 # Weishaupt-Datenpunktliste (Modbus TCP WWP) nur lesbar, die Leistungsvorgabe
                 # SollwertPV übersteuert SG-Ready ohnehin.
                 usage: Tuple[ConsumerUsage, ...] = (ConsumerUsage.SUSPENDABLE_TUNABLE,),
                 **kwargs) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or WeishauptConfiguration(), usage=usage, **kwargs)
