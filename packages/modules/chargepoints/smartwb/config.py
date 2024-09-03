from typing import Optional

from modules.common.abstract_chargepoint import SetupChargepoint


class SmartWBConfiguration:
    def __init__(self, ip_address: Optional[str] = None, timeout: int = 2):
        self.ip_address = ip_address
        self.timeout = timeout


class SmartWB(SetupChargepoint[SmartWBConfiguration]):
    def __init__(self,
                 name: str = "smartWB / EVSE-Wifi (>= v1.x.x/v2.x.x)",
                 type: str = "smartwb",
                 id: int = 0,
                 configuration: SmartWBConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SmartWBConfiguration())
