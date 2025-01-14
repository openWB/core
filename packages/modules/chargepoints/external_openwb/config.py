from typing import Optional

from modules.common.abstract_chargepoint import SetupChargepoint


class OpenWBSeriesConfiguration:
    def __init__(self, ip_address: Optional[str] = None, duo_num: int = 0):
        self.ip_address = ip_address
        self.duo_num = duo_num


class OpenWBSeries(SetupChargepoint[OpenWBSeriesConfiguration]):
    def __init__(self,
                 name: str = "Secondary openWB",
                 type: str = "external_openwb",
                 id: int = 0,
                 configuration: OpenWBSeriesConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or OpenWBSeriesConfiguration())
