from typing import Optional, Tuple
from control.consumer.consumer_data import ConsumerUsage
from helpermodules.auto_str import auto_str
from modules.common.consumer_setup import ConsumerSetup
from ..vendor import vendor_descriptor


@auto_str
class ExtraMeterOnlyConfiguration:
    def __init__(self) -> None:
        pass


@auto_str
class ExtraMeterOnly(ConsumerSetup[ExtraMeterOnlyConfiguration]):
    def __init__(self,
                 name: str = "Rein passive Messung",
                 type: str = "extra_meter_only",
                 id: int = 0,
                 configuration: Optional[ExtraMeterOnlyConfiguration] = None,
                 usage: Tuple[ConsumerUsage, ...] = (ConsumerUsage.METER_ONLY,),
                 **kwargs) -> None:
        super().__init__(name, type, id, vendor=vendor_descriptor.configuration_factory(
        ).type, configuration=configuration or ExtraMeterOnlyConfiguration(), usage=usage, **kwargs)
