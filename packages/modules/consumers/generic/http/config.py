from typing import Tuple, Optional
from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class HttpConfiguration:
    def __init__(self,
                 url: Optional[str] = None,
                 current_l1_path: Optional[str] = None,
                 current_l2_path: Optional[str] = None,
                 current_l3_path: Optional[str] = None,
                 power_path: Optional[str] = None,
                 temperatures_path: Optional[str] = None,
                 imported_path: Optional[str] = None,
                 exported_path: Optional[str] = None,
                 switch_on_path: Optional[str] = None,
                 switch_off_path: Optional[str] = None,
                 set_power_limit_path: Optional[str] = None):
        self.url = url
        self.current_l1_path = current_l1_path
        self.current_l2_path = current_l2_path
        self.current_l3_path = current_l3_path
        self.power_path = power_path
        self.temperatures_path = temperatures_path
        self.imported_path = imported_path
        self.exported_path = exported_path
        self.switch_on_path = switch_on_path
        self.switch_off_path = switch_off_path
        self.set_power_limit_path = set_power_limit_path


@auto_str
class Http(ConsumerSetup[HttpConfiguration]):
    def __init__(self,
                 name: str = "HTTP-Verbraucher",
                 type: str = "http",
                 id: int = 0,
                 configuration: Optional[HttpConfiguration] = None,
                 usage: Tuple[ConsumerUsage, ...] = (ConsumerUsage.METER_ONLY,
                                                     ConsumerUsage.CONTINUOUS,
                                                     ConsumerUsage.SUSPENDABLE_ONOFF,
                                                     ConsumerUsage.SUSPENDABLE_TUNABLE),
                 **kwargs) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or HttpConfiguration(), usage=usage, **kwargs)
