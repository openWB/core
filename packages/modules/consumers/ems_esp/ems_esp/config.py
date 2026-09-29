from typing import Optional, Tuple

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class EmsEspConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 token: Optional[str] = None):
        self.ip_address = ip_address
        self.token = token


@auto_str
class EmsEsp(ConsumerSetup[EmsEspConfiguration]):
    def __init__(self,
                 name: str = "EMS-ESP Wärmepumpe (Bosch/Buderus/Junkers)",
                 type: str = "ems_esp",
                 id: int = 0,
                 configuration: Optional[EmsEspConfiguration] = None,
                 # kein SELF_CONTROLLED: die energyPriceEl/-PV-Entities steuern laut
                 # EMS-ESP32-Quellcode die Wärmequellen-Auswahl bei Hybridanlagen, nicht die
                 # Kompressorleistung einer reinen Wärmepumpe.
                 usage: Tuple[ConsumerUsage, ...] = (ConsumerUsage.SUSPENDABLE_ONOFF,
                                                     ConsumerUsage.SUSPENDABLE_TUNABLE,
                                                     ConsumerUsage.METER_ONLY),
                 **kwargs) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or EmsEspConfiguration(), usage=usage, **kwargs)
