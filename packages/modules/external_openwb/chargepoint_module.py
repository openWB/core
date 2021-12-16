import time
from typing import Dict

from control import data
from helpermodules import pub
from modules.common.abstract_chargepoint import AbstractChargepoint
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.fault_state import ComponentInfo


def get_default_config() -> Dict:
    return {"id": 0,
            "connection_module": {
                "type": "external_openwb",
                "configuration":
                {"ip_address": "192.168.193.5",
                 "duo_num": 1
                 }
            },
            "power_module": {}}


class ChargepointModule(AbstractChargepoint):
    def __init__(self, id: int, connection_module: dict, power_module: dict) -> None:
        self.id = id
        self.connection_module = connection_module
        self.power_module = power_module
        self.component_info = ComponentInfo(
            self.id,
            "Ladepunkt", "chargepoint")

    def set_current(self, current: float) -> None:
        with SingleComponentUpdateContext(self.component_info):
            if self.connection_module["configuration"]["duo_num"] == 1:
                pub.pub_single("openWB/set/isss/Current", current,
                               hostname=self.connection_module["configuration"]["ip_address"])
            else:
                pub.pub_single("openWB/set/isss/Lp2Current", current,
                               hostname=self.connection_module["configuration"]["ip_address"])

    def get_values(self) -> None:
        with SingleComponentUpdateContext(self.component_info):
            ip_address = self.connection_module["configuration"]["ip_address"]
            cp_num = self.id
            my_ip_address = data.data.system_data["system"].data["ip_address"]
            pub.pub_single("openWB/set/isss/heartbeat", 0, hostname=ip_address)
            pub.pub_single("openWB/set/isss/parentWB", my_ip_address,
                           hostname=ip_address, no_json=True)
            if (self.connection_module["configuration"]["duo_num"] == 2):
                pub.pub_single("openWB/set/isss/parentCPlp2", str(cp_num), hostname=ip_address)
            else:
                pub.pub_single("openWB/set/isss/parentCPlp1", str(cp_num), hostname=ip_address)

    def switch_phases(self, phases_to_use: int, duration: int) -> None:
        with SingleComponentUpdateContext(self.component_info):
            pub.pub_single("openWB/set/isss/U1p3p", phases_to_use,
                           self.connection_module["configuration"]["ip_address"])
            time.sleep(6+duration-1)
