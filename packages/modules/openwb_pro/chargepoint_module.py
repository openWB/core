
import logging
import time
from typing import Dict

from modules.common.abstract_chargepoint import AbstractChargepoint
from modules.common.component_context import ErrorCounterContext, SingleComponentUpdateContext
from modules.common.fault_state import ComponentInfo
from modules.common.store import get_chargepoint_value_store
from modules.common.component_state import ChargepointState
from modules.common import req

log = logging.getLogger(__name__)


def get_default_config() -> Dict:
    return {"id": 0,
            "connection_module": {
                "type": "openwb_pro",
                "name": "openWB Pro",
                "configuration": {
                    "ip_address": None
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
        self.__session = req.get_http_session()
        self.__client_error_context = ErrorCounterContext(
            "Anhaltender Fehler beim Auslesen des Ladepunkts. Sollstromstärke wird zurückgesetzt.")

        with SingleComponentUpdateContext(self.component_info, False):
            with self.__client_error_context:
                self.__session.post(
                    'http://' + self.connection_module["configuration"]["ip_address"] + '/connect.php',
                    data={'heartbeatenabled': '1'})

    def set_current(self, current: float) -> None:
        if self.__client_error_context.error_counter_exceeded():
            current = 0
        with SingleComponentUpdateContext(self.component_info, False):
            with self.__client_error_context:
                ip_address = self.connection_module["configuration"]["ip_address"]
                self.__session.post('http://'+ip_address+'/connect.php', data={'ampere': current})

    def get_values(self) -> None:
        with SingleComponentUpdateContext(self.component_info):
            with self.__client_error_context:
                ip_address = self.connection_module["configuration"]["ip_address"]
                json_rsp = self.__session.get('http://'+ip_address+'/api2.php').json()
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
                self.__client_error_context.reset_error_counter()

    def switch_phases(self, phases_to_use: int, duration: int) -> None:
        with SingleComponentUpdateContext(self.component_info, False):
            with self.__client_error_context:
                ip_address = self.connection_module["configuration"]["ip_address"]
                response = self.__session.get('http://'+ip_address+'/api2.php')
                if response.json()["phases_target"] != phases_to_use:
                    ip_address = self.connection_module["configuration"]["ip_address"]
                    self.__session.post('http://'+ip_address+'/connect.php',
                                        data={'phasetarget': str(phases_to_use)})
                    time.sleep(duration)
