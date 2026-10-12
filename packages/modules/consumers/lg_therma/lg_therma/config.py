from typing import Optional, Tuple

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class LgThermaConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: int = 502,
                 modbus_id: int = 33):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id


@auto_str
class LgTherma(ConsumerSetup[LgThermaConfiguration]):
    def __init__(self,
                 name: str = "LG Therma V Wärmepumpe",
                 type: str = "lg_therma",
                 id: int = 0,
                 configuration: Optional[LgThermaConfiguration] = None,
                 # UNVERIFIZIERT: keine offizielle LG-Dokumentation für dieses Register gefunden.
                 # PI-485-Protokoll selbst ist offiziell dokumentiert.
                 usage: Tuple[ConsumerUsage, ...] = (ConsumerUsage.SUSPENDABLE_ONOFF,
                                                     ConsumerUsage.METER_ONLY),
                 **kwargs) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or LgThermaConfiguration(), usage=usage, **kwargs)
