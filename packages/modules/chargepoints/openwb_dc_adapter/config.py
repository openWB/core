from typing import Optional

from helpermodules import hardware_configuration
from modules.common.abstract_chargepoint import SetupChargepoint


class OpenWBDcAdapterConfiguration:
    def __init__(self, ip_address: Optional[str] = None):
        self.ip_address = ip_address


class OpenWBDcAdapter(SetupChargepoint[OpenWBDcAdapterConfiguration]):
    def __init__(self,
                 name: str = "openWB Adapter für DC-Lader",
                 type: str = "openwb_dc_adapter",
                 id: int = 0,
                 configuration: OpenWBDcAdapterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or OpenWBDcAdapterConfiguration())
        self.visibility = hardware_configuration.get_hardware_configuration_setting("dc_charging")
        self.charging_type = "DC"
