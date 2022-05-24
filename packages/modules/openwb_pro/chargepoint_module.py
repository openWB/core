
import logging
import time
import requests
from typing import Dict

from modules.common.abstract_chargepoint import AbstractChargepoint
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.fault_state import ComponentInfo
from modules.common.store import get_chargepoint_value_store
from modules.common.component_state import ChargepointState

log = logging.getLogger(__name__)


def get_default_config() -> Dict:
    return {"id": 0,
            "connection_module": {
                "type": "openwb_pro",
                "name": "openWB Pro",
                "configuration":
                {"ip_address": "192.168.1.85"
                 }
            },
            "power_module": {}}


class ChargepointModule(AbstractChargepoint):
    def __init__(self, id: int, connection_module: dict, power_module: dict) -> None:
        self.id = id
        self.connection_module = connection_module
        self.power_module = power_module
        self.__store = get_chargepoint_value_store(self.id)
        self.component_info = ComponentInfo(
            self.id,
            "Ladepunkt", "chargepoint")

        with SingleComponentUpdateContext(self.component_info):
            response = requests.post(
                'http://' + self.connection_module["configuration"]["ip_address"] + '/connect.php',
                data={'heartbeatenabled': '1'})
            response.raise_for_status()

    def set_current(self, current: float) -> None:
        with SingleComponentUpdateContext(self.component_info):
            ip_address = self.connection_module["configuration"]["ip_address"]
            response = requests.post('http://'+ip_address+'/connect.php', data={'ampere': current})
            response.raise_for_status()

    def get_values(self) -> None:
        with SingleComponentUpdateContext(self.component_info):
            ip_address = self.connection_module["configuration"]["ip_address"]
            response = requests.get('http://'+ip_address+'/api2.php')
            response.raise_for_status()
            json_rsp = response.json()
            log.debug("openWB Pro "+str(self.id)+": "+str(json_rsp))

            chargepoint_state = ChargepointState(
                power=json_rsp["power_all"],
                currents=json_rsp["currents"],
                imported=json_rsp["imported"],
                exported=json_rsp["exported"],
                plug_state=json_rsp["plug_state"],
                charge_state=json_rsp["charge_state"],
                phases_in_use=json_rsp["phases_in_use"]
            )

            self.__store.set(chargepoint_state)

    def switch_phases(self, phases_to_use: int, duration: int) -> None:
        with SingleComponentUpdateContext(self.component_info):
            ip_address = self.connection_module["configuration"]["ip_address"]
            response = requests.get('http://'+ip_address+'/api2.php')
            response.raise_for_status()
            if response.json()["phases_target"] != phases_to_use:
                ip_address = self.connection_module["configuration"]["ip_address"]
                response = requests.post('http://'+ip_address+'/connect.php', data={'phasetarget': str(phases_to_use)})
                response.raise_for_status()
                time.sleep(duration)
