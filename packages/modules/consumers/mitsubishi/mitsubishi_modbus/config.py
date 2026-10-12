from typing import Optional, Tuple

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class MitsubishiModbusConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: int = 502,
                 modbus_id: int = 1):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id


@auto_str
class MitsubishiModbus(ConsumerSetup[MitsubishiModbusConfiguration]):
    def __init__(self,
                 name: str = "Mitsubishi Electric Klimaanlage (Intesis Modbus-Interface)",
                 type: str = "mitsubishi_modbus",
                 id: int = 0,
                 configuration: Optional[MitsubishiModbusConfiguration] = None,
                 usage: Tuple[ConsumerUsage, ...] = (ConsumerUsage.SUSPENDABLE_ONOFF,),
                 **kwargs) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or MitsubishiModbusConfiguration(), usage=usage, **kwargs)
