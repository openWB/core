from typing import List

from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class HttpConfiguration:
    def __init__(self, url=None,
                 current_l1_path=None,
                 current_l2_path=None,
                 current_l3_path=None,
                 power_path=None,
                 temperatures_path=None,
                 imported_path=None,
                 exported_path=None):
        self.url = url
        self.current_l1_path = current_l1_path
        self.current_l2_path = current_l2_path
        self.current_l3_path = current_l3_path
        self.power_path = power_path
        self.temperatures_path = temperatures_path
        self.imported_path = imported_path
        self.exported_path = exported_path


@auto_str
class Http(ConsumerSetup[HttpConfiguration]):
    def __init__(self,
                 name: str = "HTTP",
                 type: str = "http",
                 id: int = 0,
                 configuration: HttpConfiguration = None,
                 usage: List[ConsumerUsage] = [ConsumerUsage.METER_ONLY]) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or HttpConfiguration(), usage=usage)
