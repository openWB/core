from typing import Optional, Tuple

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class LuxtronikConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: int = 502,
                 modbus_id: int = 1,
                 # Anhebung von Heiz- und Warmwassersolltemperatur im Überschussbetrieb [K] -
                 # abhängig vom Heizsystem (Fußbodenheizung/Heizkörper, Puffergröße), daher
                 # bewusst konfigurierbar statt fest verdrahtet.
                 boost_offset: float = 5.0):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id
        self.boost_offset = boost_offset


@auto_str
class Luxtronik(ConsumerSetup[LuxtronikConfiguration]):
    def __init__(self,
                 name: str = "Luxtronik 2.1 Wärmepumpe (Alpha Innotec/Buderus Logamatic HMC/Novelan/Roth/Wolf u.a.)",
                 type: str = "luxtronik",
                 id: int = 0,
                 configuration: Optional[LuxtronikConfiguration] = None,
                 usage: Tuple[ConsumerUsage, ...] = (ConsumerUsage.SUSPENDABLE_ONOFF,
                                                     ConsumerUsage.METER_ONLY),
                 **kwargs) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or LuxtronikConfiguration(), usage=usage, **kwargs)
