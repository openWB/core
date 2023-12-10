import datetime
import logging
import dataclasses
import copy

from datetime import timedelta

from control import data, yourcharge
from control.algorithm.yourcharge.heartbeat_checker import HeartbeatChecker
from control.algorithm.yourcharge.standard_socket_handler import StandardSocketHandler, StandardSocketStatus
from helpermodules.subdata import SubData
from helpermodules.pub import Pub
from modules.internal_chargepoint_handler.internal_chargepoint_handler import GeneralInternalChargepointHandler
from modules.internal_chargepoint_handler.internal_chargepoint_handler_config import RfidData

log = logging.getLogger(__name__)


class AlgorithmYc():

    def __init__(self, general_chargepoint_handler: GeneralInternalChargepointHandler):
        (key, value) = next(((key, value) for i, (key, value) in enumerate(data.data.cp_data.items()) if value.chargepoint_module.config.type == 'internal_openwb'), None)
        self.__internal_cp = value
        self.__internal_cp_key = key
        self.__general_cp_handler = general_chargepoint_handler
        self.__heartbeat_checker: HeartbeatChecker = HeartbeatChecker(timedelta(seconds=25))
        self.__heartbeat_status: bool = None
        self.__previous_heartbeat_status: bool = None
        self.__lm_status: yourcharge.LmStatus = None
        self.__previous_lm_status = None
        self.__last_control_run = datetime.datetime(1, 1, 1, 0, 0, 0)
        self.__standard_socket_handler: StandardSocketHandler = StandardSocketHandler(general_chargepoint_handler)
        log.critical(f"YC algorithm active: Internal CP found as '{self.__internal_cp_key}'")


    def calc_current(self) -> None:

        try:
            # check heartbeat and super-early exit in case of controller not being seen anymore, charge current --> 0 and socket --> off
            self.__heartbeat_status = self.__heartbeat_checker.is_heartbeat_timeout()
            if self.__heartbeat_status == False:
                log.critical(f"Detected controller heartbeat timeout: Disabling charge immediately")
                self.__internal_cp.data.set.current = 0
                self.__standard_socket_handler.socket_off()
                self.__lm_status = yourcharge.LmStatus.DownByError
                return

            # very early exit in case of box being administratively disabled, charge current --> 0 and socket --> off
            if data.data.yc_data.data.yc_config.active != True:
                log.info(f"Box is administratively disabled: Disabling charge immediately")
                self.__internal_cp.data.set.current = 0
                self.__standard_socket_handler.socket_off()
                self.__lm_status = yourcharge.LmStatus.DownByDisable
                return

            # handle re-appearing heartbeat
            if self.__previous_heartbeat_status != self.__heartbeat_status:
                log.critical(f"Controller heartbeat returned: Trying to restore previous state")
                self.__standard_socket_handler.restore_previous()

            # check if control interval is hit
            now_it_is = datetime.datetime.utcnow()
            if (now_it_is - self.__last_control_run).total_seconds() < data.data.yc_data.data.yc_config.minimum_adjustment_interval:
                log.info(f"Control loop not yet due")
                return
            self.__last_control_run = now_it_is

            # get data that we need
            rfid_data: RfidData = SubData.internal_chargepoint_data["rfid_data"]
            log.info(f"rfid_data = {rfid_data}")

            # handle standard socket control statemachine
            self.__standard_socket_handler.handle_socket_algorithm(rfid_data)
            if not self.__standard_socket_handler.can_ev_charge():
                return

            # handle supersede or regular control
            if data.data.yc_data.data.yc_control.fixed_charge_current is None:
                log.info(f"Regular load control requested by yc_data.data.yc_control.fixed_charge_current == {data.data.yc_data.datayc_control.fixed_charge_current}")
                self.do_load_control()
            else:
                # handling of superseded, fixed charge current
                if data.data.yc_data.data.yc_control.fixed_charge_current < 0.0:
                    # invalid or default value < 0.0
                    log.info(f"Charging disapproved by yc_data.data.yc_control.fixed_charge_current: Setting CP '{self.__internal_cp_key}' to 0 A")
                    self.__internal_cp.data.set.current = 0
                    self.__lm_status = yourcharge.LmStatus.Superseded
                else:
                    # fixed value >= 0.0 provided
                    log.info(f"Fixed current requested by yc_data.data.yc_control.fixed_charge_current: Setting CP '{self.__internal_cp_key}' to {data.data.yc_data.data.yc_control.fixed_charge_current} A")
                    self.__internal_cp.data.set.current = data.data.yc_data.data.yc_control.fixed_charge_current
                    self.__lm_status = yourcharge.LmStatus.Superseded

        finally:
            self.send_status()
            self.__previous_heartbeat_status = self.__heartbeat_status
            SubData.internal_chargepoint_data["rfid_data"].last_tag = ""


    def send_status(self):
        if self.__previous_heartbeat_status != self.__heartbeat_status:
            Pub().pub(f"{yourcharge.yc_status_topic}/heartbeat", self.__heartbeat_status)
            self.__previous_heartbeat_status = self.__heartbeat_status
        if self.__previous_lm_status != self.__lm_status:
            Pub().pub(f"{yourcharge.yc_status_topic}/lm_status", self.__lm_status)
            self.__previous_lm_status = self.__lm_status
        if self.__standard_socket_handler is not None:
            if  self.__standard_socket_handler.get_data() is not None and self.__standard_socket_handler.get_data().imported_wh is not None:
                Pub().pub(f"{yourcharge.yc_status_topic}/standard_socket", dataclasses.asdict(self.__standard_socket_handler.get_data()))


    def do_load_control(self):
        log.info(f"Regular load control NOT YET IMPLEMENTED")
