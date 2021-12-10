
import time
import requests
from typing import Dict

from modules.common.abstract_chargepoint import AbstractChargepoint
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.fault_state import ComponentInfo
from modules.common.store import get_chargepoint_value_store
from packages.modules.common.component_state import ChargepointState


def get_default_config() -> Dict:
    return {"connection_module": {
        "type": "openwb_pro",
        "configuration":
        {"ip_address": "192.168.1.100",
         "id": 0}
    },
        "power_module": {}}


class ChargepointModule(AbstractChargepoint):
    def __init__(self, connection_module: dict, power_module: dict) -> None:
        self.connection_module = connection_module
        self.power_module = power_module
        self.__store = get_chargepoint_value_store(self.connection_module["configuration"]["id"])
        self.component_info = ComponentInfo(
            self.connection_module["configuration"]["id"],
            "Ladepunkt", "chargepoint")

    def set_current(self, current: float) -> None:
        with SingleComponentUpdateContext(self.component_info):
            ip_address = self.connection_module["configuration"]["ip_address"]
            response = requests.post('http://'+ip_address+'/connect.php', data={'ampere': current})
            response.raise_for_status()

    def get_values(self) -> None:
        with SingleComponentUpdateContext(self.component_info):
            ip_address = self.connection_module["configuration"]["ip_address"]
            response = requests.post('http://'+ip_address+'/connect.php', data={'heartbeatenabled': '1'})
            response.raise_for_status()
            response = requests.get('http://'+ip_address+'/api2.php')
            response.raise_for_status()
            json_rsp = response.json()

            chargepoint_state = ChargepointState(
                power_all=json_rsp["power_all"],
                currents=json_rsp["currents"],
                imported=json_rsp["imported"],
                counter=json_rsp["exported"],
                plug_state=json_rsp["plug_state"],
                charge_state=json_rsp["charge_state"],
                phases_in_use=json_rsp["phases_in_use"]
            )

            self.__store.set(chargepoint_state)

    def switch_phases(self, phases_to_use: int, duration: int) -> None:
        with SingleComponentUpdateContext(self.component_info):
            ip_address = self.connection_module["configuration"]["ip_address"]
            response = requests.post('http://'+ip_address+'/connect.php', data={'phasetarget': str(phases_to_use)})
            response.raise_for_status()
            time.sleep(6+duration-1)
