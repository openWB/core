
import logging
import time

from helpermodules.utils.error_counter import ErrorCounterContext
from modules.chargepoints.openwb_pro.config import OpenWBPro
from modules.common.abstract_chargepoint import AbstractChargepoint
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.fault_state import ComponentInfo
from modules.common.store import get_chargepoint_value_store
from modules.common.component_state import ChargepointState
from modules.common import req

log = logging.getLogger(__name__)


class ChargepointModule(AbstractChargepoint):
    def __init__(self, config: OpenWBPro) -> None:
        self.config = config
        self.store = get_chargepoint_value_store(self.config.id)
        self.component_info = ComponentInfo(
            self.config.id,
            "Ladepunkt", "chargepoint")
        self.__session = req.get_http_session()
        self.__client_error_context = ErrorCounterContext(
            "Anhaltender Fehler beim Auslesen des Ladepunkts. Sollstromstärke wird zurückgesetzt.")

        with SingleComponentUpdateContext(self.component_info, False):
            with self.__client_error_context:
                self.__session.post(
                    'http://' + self.config.configuration.ip_address + '/connect.php',
                    data={'heartbeatenabled': '1'})

    def set_current(self, current: float) -> None:
        if self.__client_error_context.error_counter_exceeded():
            current = 0
        with SingleComponentUpdateContext(self.component_info, False):
            with self.__client_error_context:
                ip_address = self.config.configuration.ip_address
                self.__session.post('http://'+ip_address+'/connect.php', data={'ampere': current})

    def get_values(self) -> None:
        with SingleComponentUpdateContext(self.component_info):
            with self.__client_error_context:
                ip_address = self.config.configuration.ip_address
                json_rsp = self.__session.get('http://'+ip_address+'/connect.php').json()

                chargepoint_state = ChargepointState(
                    power=json_rsp["power_all"],
                    currents=json_rsp["currents"],
                    imported=json_rsp["imported"],
                    exported=json_rsp["exported"],
                    plug_state=json_rsp["plug_state"],
                    charge_state=json_rsp["charge_state"],
                    phases_in_use=json_rsp["phases_in_use"],
                    rfid=json_rsp["vehicle_id"]
                )

                self.store.set(chargepoint_state)
                self.__client_error_context.reset_error_counter()

    def switch_phases(self, phases_to_use: int, duration: int) -> None:
        with SingleComponentUpdateContext(self.component_info, False):
            with self.__client_error_context:
                ip_address = self.config.configuration.ip_address
                response = self.__session.get('http://'+ip_address+'/connect.php')
                if response.json()["phases_target"] != phases_to_use:
                    ip_address = self.config.configuration.ip_address
                    self.__session.post('http://'+ip_address+'/connect.php',
                                        data={'phasetarget': str(1 if phases_to_use == 1 else 3)})
                    time.sleep(duration)

    def clear_rfid(self) -> None:
        with SingleComponentUpdateContext(self.component_info, False):
            with self.__client_error_context:
                log.debug("Die openWB-Pro unterstützt keine RFID-Tags.")


chargepoint_descriptor = DeviceDescriptor(configuration_factory=OpenWBPro)
