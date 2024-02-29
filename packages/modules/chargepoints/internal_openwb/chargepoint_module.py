from modules.chargepoints.internal_openwb.config import InternalOpenWB
from modules.chargepoints.external_openwb.chargepoint_module import ChargepointModule as ChargepointModuleSeries
from modules.common.abstract_device import DeviceDescriptor


class ChargepointModule(ChargepointModuleSeries):
    def __init__(self, config: InternalOpenWB) -> None:
        super().__init__(config)


chargepoint_descriptor = DeviceDescriptor(configuration_factory=InternalOpenWB)
