
from typing import Dict

from helpermodules import timecheck
from modules.common.abstract_chargepoint import AbstractChargepoint
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.fault_state import ComponentInfo
from modules.common.store import get_chargepoint_value_store
from modules.common.component_state import ChargepointState
from modules.common import req


def get_default_config() -> Dict:
    return {
        "id": 0,
        "connection_module": {
            "type": "smartwb",
            "name": "smartWB / EVSE-Wifi (>= v1.x.x/v2.x.x)",
            "configuration": {
                    "ip_address": None,
                    "timeout": 2
            }
        },
        "power_module": {}
    }


class ChargepointModule(AbstractChargepoint):
    def __init__(self, id: int, connection_module: dict, power_module: dict) -> None:
        self.id = id
        self.connection_module = connection_module
        self.power_module = power_module
        self.__store = get_chargepoint_value_store(self.id)
        self.component_info = ComponentInfo(
            self.id,
            "Ladepunkt", "chargepoint")

    def set_current(self, current: float) -> None:
        with SingleComponentUpdateContext(self.component_info):
            ip_address = self.connection_module["configuration"]["ip_address"]
            timeout = self.connection_module["configuration"]["timeout"]
            params = (
                ('current', '$current'),
            )
            req.get_http_session().get('http://'+ip_address+'/setCurrent', params=params, timeout=(timeout, None))

    def get_values(self) -> None:
        with SingleComponentUpdateContext(self.component_info):
            ip_address = self.connection_module["configuration"]["ip_address"]
            timeout = self.connection_module["configuration"]["timeout"]
            response = req.get_http_session().get('http://'+ip_address+'/getParameters', timeout=timeout)
            json_rsp = response.json()["list"][0]

            ev_state = json_rsp["vehicleState"]
            if ev_state == 3:
                charge_state = True
                plug_state = True
            elif ev_state == 2:
                charge_state = False
                plug_state = True
            else:
                charge_state = False
                plug_state = False

            chargepoint_state = ChargepointState(
                power=json_rsp["actualPower"] / 1000,
                currents=[json_rsp["currentP1"], json_rsp["currentP2"], json_rsp["currentP3"]],
                imported=json_rsp["meterReading"],
                plug_state=plug_state,
                charge_state=charge_state,
                phases_in_use=json_rsp["phases_in_use"]
            )

            if json_rsp["RFIDUID"] >= 3:
                chargepoint_state.read_tag = {
                    "read_tag": str(json_rsp["RFIDUID"]),
                    "timestamp": timecheck.create_timestamp()}

            self.__store.set(chargepoint_state)
