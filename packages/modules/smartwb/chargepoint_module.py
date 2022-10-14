
from typing import Dict

from modules.common.abstract_chargepoint import AbstractChargepoint
from modules.common.component_context import ErrorCounterContext, SingleComponentUpdateContext
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
        self.store = get_chargepoint_value_store(self.id)
        self.component_info = ComponentInfo(
            self.id,
            "Ladepunkt", "chargepoint")
        self.__client_error_context = ErrorCounterContext(
            "Anhaltender Fehler beim Auslesen des Ladepunkts. Soll-Stromstärke wird zurückgesetzt.")
        self.phases_in_use = 1

    def set_current(self, current: float) -> None:
        if self.__client_error_context.error_counter_exceeded():
            current = 0
        with SingleComponentUpdateContext(self.component_info, False):
            with self.__client_error_context:
                ip_address = self.connection_module["configuration"]["ip_address"]
                timeout = self.connection_module["configuration"]["timeout"]
                # Stromvorgabe in Hundertstel Ampere
                params = (('current', int(current*100)),)
                req.get_http_session().get('http://'+ip_address+'/setCurrent', params=params, timeout=(timeout, None))

    def get_values(self) -> None:
        with SingleComponentUpdateContext(self.component_info):
            with self.__client_error_context:
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

                currents = [json_rsp["currentP1"], json_rsp["currentP2"], json_rsp["currentP3"]]

                if currents[2] > 3:
                    self.phases_in_use = 3
                elif currents[1] > 3:
                    self.phases_in_use = 2
                elif currents[0] > 3:
                    self.phases_in_use = 1

                chargepoint_state = ChargepointState(
                    power=json_rsp["actualPower"] * 1000,
                    currents=currents,
                    imported=json_rsp["meterReading"] * 1000,
                    plug_state=plug_state,
                    charge_state=charge_state,
                    phases_in_use=self.phases_in_use
                )

                if json_rsp.get("RFIDUID"):
                    if json_rsp["RFIDUID"] == "":
                        tag = None
                    else:
                        tag = json_rsp["RFIDUID"]
                    chargepoint_state.rfid = tag

                if json_rsp.get("voltageP1"):
                    chargepoint_state.voltages = [json_rsp["voltageP1"], json_rsp["voltageP2"], json_rsp["voltageP3"]]

                self.store.set(chargepoint_state)
                self.__client_error_context.reset_error_counter()

    def clear_rfid(self) -> None:
        with SingleComponentUpdateContext(self.component_info):
            with self.__client_error_context:
                ip_address = self.connection_module["configuration"]["ip_address"]
                timeout = self.connection_module["configuration"]["timeout"]
                req.get_http_session().get('http://'+ip_address+'/clearRfid', timeout=(timeout, None))
