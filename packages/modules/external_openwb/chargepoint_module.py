from typing import Dict

from control import data
from helpermodules.log import MainLogger
from helpermodules import pub
from modules.common.abstract_chargepoint import AbstractChargepoint


def get_default_config() -> Dict:
    return {"connection_module": {
        "type": "external_openwb",
        "configuration":
        {"ip_address": "192.168.193.5",
         "duo_num": 1,
         "id": 0}
    },
        "power_module": {}}


class ChargepointModule(AbstractChargepoint):
    def __init__(self, connection_module: dict, power_module: dict) -> None:
        self.connection_module = connection_module
        self.power_module = power_module

    def set_current(self, current: float) -> None:
        try:
            if self.connection_module["configuration"]["duo_num"] == 1:
                pub.pub_single("openWB/set/isss/Current", current,
                               hostname=self.connection_module["configuration"]["ip_address"])
            else:
                pub.pub_single("openWB/set/isss/Lp2Current", current,
                               hostname=self.connection_module["configuration"]["ip_address"])
        except Exception:
            MainLogger().exception("Fehler im Modul der externen openWB")

    def get_values(self) -> None:
        try:
            ip_address = self.connection_module["configuration"]["ip_address"]
            cp_num = self.connection_module["configuration"]["id"]
            my_ip_address = data.data.system_data["system"].data["ip_address"]
            pub.pub_single("openWB/set/isss/heartbeat", 0, hostname=ip_address)
            pub.pub_single("openWB/set/isss/parentWB", my_ip_address,
                           hostname=ip_address, no_json=True)
            if (self.connection_module["configuration"]["duo_num"] == 2):
                pub.pub_single("openWB/set/isss/parentCPlp2", str(cp_num), hostname=ip_address)
            else:
                pub.pub_single("openWB/set/isss/parentCPlp1", str(cp_num), hostname=ip_address)
        except Exception:
            MainLogger().exception("Fehler im Modul der externen openWB")
