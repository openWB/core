from typing import Optional, Tuple

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class EspHomeConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 power_sensor_name: Optional[str] = None,
                 switch_name: Optional[str] = None):
        self.ip_address = ip_address
        self.power_sensor_name = power_sensor_name
        self.switch_name = switch_name


@auto_str
class EspHome(ConsumerSetup[EspHomeConfiguration]):
    def __init__(self,
                 name: str = "ESPHome",
                 type: str = "esphome",
                 id: int = 0,
                 configuration: Optional[EspHomeConfiguration] = None,
                 usage: Tuple[ConsumerUsage, ...] = (ConsumerUsage.SUSPENDABLE_ONOFF,
                                                     ConsumerUsage.METER_ONLY),
                 **kwargs) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or EspHomeConfiguration(), usage=usage, **kwargs)
