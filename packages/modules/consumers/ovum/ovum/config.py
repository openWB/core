from typing import Optional, Tuple
 
from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor
 
 
@auto_str
class OvumConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: Optional[int] = 502,
                 modbus_id: Optional[int] = 1):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id
 
 
@auto_str
class Ovum(ConsumerSetup[OvumConfiguration]):
    def __init__(self,
                 name: str = "OVUM Wärmepumpe (CubeSpeicher/MPlus)",
                 type: str = "ovum",
                 id: int = 0,
                 configuration: OvumConfiguration = None,
                 # OVUM unterstützt eine echte Leistungsvorgabe (SUSPENDABLE_TUNABLE),
                 # Eigenregelung anhand der Systemwerte (SELF_CONTROLLED) sowie
                 # SG-Ready-Ein-/Ausschalten (SUSPENDABLE_ONOFF)
                 usage: Tuple[ConsumerUsage, ...] = (ConsumerUsage.SUSPENDABLE_TUNABLE,
                                                     ConsumerUsage.SELF_CONTROLLED,
                                                     ConsumerUsage.SUSPENDABLE_ONOFF,
                                                     ConsumerUsage.METER_ONLY),
                 **kwargs) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or OvumConfiguration(), usage=usage, **kwargs)
 