import datetime
from enum import Enum
import logging
import dataclasses

from datetime import timedelta

from control import data, yourcharge
from control.algorithm.yourcharge.heartbeat_checker import HeartbeatChecker
from control.algorithm.yourcharge.standard_socket_handler import StandardSocketHandler, StandardSocketStatus
from control.algorithm.yourcharge.status_handler import YcStatusHandler
from helpermodules.subdata import SubData
from helpermodules.pub import Pub
from modules.internal_chargepoint_handler.internal_chargepoint_handler import GeneralInternalChargepointHandler
from modules.internal_chargepoint_handler.internal_chargepoint_handler_config import RfidData


log = logging.getLogger(__name__)


class LoadControlState(int, Enum):
    Startup = 0
    Idle = 1
    SocketActive = 2
    WaitingForPlugin = 3
    EvActive = 4
    HeartbeatTimeout = 5
    Disabled = 6

class AlgorithmYc():

    def __init__(self, general_chargepoint_handler: GeneralInternalChargepointHandler):
        (key, value) = next(((key, value) for i, (key, value) in enumerate(data.data.cp_data.items()) if value.chargepoint_module.config.type == 'internal_openwb'), None)
        self._status_handler: YcStatusHandler = YcStatusHandler()
        self._internal_cp = value
        self._internal_cp_key = key
        self._load_control_state = LoadControlState.Startup
        self._wait_for_socket_idle = False
        self._general_cp_handler = general_chargepoint_handler
        self._heartbeat_checker: HeartbeatChecker = HeartbeatChecker(timedelta(seconds=25))
        self._last_control_run = datetime.datetime(1, 1, 1, 0, 0, 0)
        self._standard_socket_handler: StandardSocketHandler = StandardSocketHandler(general_chargepoint_handler, self._status_handler)
        log.critical(f"YC algorithm active: Internal CP found as '{self._internal_cp_key}'")


    def perform_load_control(self) -> None:

        try:

            # check heartbeat and super-early exit in case of controller not being seen anymore, charge current --> 0 and socket --> off
            self._status_handler.update_heartbeat_ok(self._heartbeat_checker.is_heartbeat_ok())

            # copy cp-enabled state from control (and persistence) area to current status (which gets used subsequently)
            # current status implictly updates control when changed
            # this way the cp-enabled status gets persisted in MQTT server
            self._status_handler.update_cp_enabled(data.data.yc_data.data.yc_control.cp_enabled)

            # get data that we need
            rfid_data: RfidData = SubData.internal_chargepoint_data["rfid_data"]
            log.info(f"rfid_data = {rfid_data}")

            if not self._status_handler.get_heartbeat_ok():
                # unconditional early exit in case of heartbeat timeout: charge current --> 0 and socket --> off
                self._transition_to_heartbeat_timeout()
            elif not data.data.yc_data.data.yc_config.active:
                # unconditional early exit in case of box being administratively disabled: charge current --> 0 and socket --> off
                self._transition_to_disabled()
            elif self._current_control_state == LoadControlState.Startup:
                self._check_startup_transitions()
            elif self._current_control_state == LoadControlState.Idle:
                self._check_idle_transitions()
            elif self._current_control_state == LoadControlState.SocketActive:
                self._check_socket_active_transitions()
            elif self._current_control_state == LoadControlState.WaitingForPlugin:
                self._check_wait_for_plugin_transitions()
            elif self._current_control_state == LoadControlState.EvActive:
                self._check_ev_active_transitions()
            elif self._current_control_state == LoadControlState.HeartbeatTimeout:
                self._check_heartbeat_timeout_transitions()
            elif self._current_control_state == LoadControlState.Disabled:
                self._check_disabled_transitions()
            else:
                log.critical(f"Unknown state '{self._current_control_state.name}': Resetting to Idle")
                self._current_control_state = LoadControlState.Idle


            # handle standard socket control statemachine
            valid_standard_socket_tag_found = self._standard_socket_handler.handle_socket_algorithm(rfid_data)
            if valid_standard_socket_tag_found:
                # immediately disable CP when valid standard socket tag has been found
                self._status_handler.update_cp_enabled(False)
            else:
                # check if EV RFID tag has been found
                if self._valid_ev_rfid_scanned(rfid_data):
                    self._standard_socket_handler.socket_off()
                    self._wait_for_socket_idle = True
                if not self._standard_socket_handler.can_ev_charge():
                    # immediately disable CP socket handler signales that EV must not charge
                    self._status_handler.update_cp_enabled(False)
            if self._wait_for_socket_idle and not self._status_handler.get_cp_enabled() and self._standard_socket_handler.can_ev_charge():
                self._status_handler.update_cp_enabled(True)
                self._wait_for_socket_idle = False

            # handle supersede or regular control
            if not self._standard_socket_handler.can_ev_charge():
                self._set_current("EV chargepoint disabled", 0.0, yourcharge.LmStatus.DownForSocket)
            elif not self._status_handler.get_cp_enabled():
                self._set_current("EV chargepoint disabled", 0.0, yourcharge.LmStatus.DownByDisable)
                return
            elif data.data.yc_data.data.yc_control.fixed_charge_current is None:
                log.info(f"Regular load control requested by yc_data.data.yc_control.fixed_charge_current == {data.data.yc_data.datayc_control.fixed_charge_current}")
                self._do_load_control()
            else:
                # handling of superseded, fixed charge current
                if data.data.yc_data.data.yc_control.fixed_charge_current < 0.0:
                    # invalid or default value < 0.0
                    self._set_current("Charging disapproved by yc_data.data.yc_control.fixed_charge_current", 0.0, yourcharge.LmStatus.DownByError)
                else:
                    # fixed value >= 0.0 provided
                    log.info(f": Setting CP '{self._internal_cp_key}' charge current to {data.data.yc_data.data.yc_control.fixed_charge_current} A")
                    self._set_current("Fixed current requested by yc_data.data.yc_control.fixed_charge_current", data.data.yc_data.data.yc_control.fixed_charge_current, yourcharge.LmStatus.Superseded)

        finally:
            self._send_status()
            SubData.internal_chargepoint_data["rfid_data"].last_tag = ""


    ### transition checks ###
    def _check_idle_transitions(self):
        pass


    def _check_disabled_transitions(self):
        # handle re-activation
        if data.data.yc_data.data.yc_config.active:
            log.critical(f"Controller heartbeat returned: Trying to restore previous state")
            self._standard_socket_handler.restore_previous()
            self._load_control_state = LoadControlState.Idle


    def _check_startup_transitions(self):
        self._standard_socket_handler.restore_previous()
        self._load_control_state = self._derive_state()


    def _check_heartbeat_timeout_transitions(self):
        # handle re-appearing heartbeat
        if self._status_handler.has_changed_heartbeat():
            log.critical(f"Controller heartbeat returned: Trying to restore previous state")
            self._standard_socket_handler.restore_previous()
            self._load_control_state = self._derive_state()


    def _derive_state(self) -> LoadControlState:
        if data.data.yc_data.data.yc_control.cp_enabled:
            if self._standard_socket_handler.can_ev_charge():
                if self._internal_cp.data.get.plug_state:
                    self._load_control_state = LoadControlState.EvActive
                else:
                    self._load_control_state = LoadControlState.WaitingForPlugin
            else:
                self._load_control_state = LoadControlState.SocketActive
        else:
            if self._standard_socket_handler.can_ev_charge():
                self._load_control_state = LoadControlState.Idle
            else:
                self._load_control_state = LoadControlState.SocketActive


    ### transition actions ###
    def _transition_to_disabled(self):
        self._set_current("Box is administratively disabled: Disabling charge immediately", 0.0, yourcharge.LmStatus.DownByDisable)
        self._standard_socket_handler._socket_off()
        self._load_control_state = LoadControlState.Disabled


    def _transition_to_heartbeat_timeout(self):
        self._set_current("Detected controller heartbeat timeout: Disabling charge immediately", 0.0, yourcharge.LmStatus.DownByError)
        self._standard_socket_handler._socket_off()
        self._load_control_state = LoadControlState.HeartbeatTimeout


    ### other, non-statemachine, methods
    def _set_current(self, justification: str, current: float, status: yourcharge.LmStatus):
        self._status_handler.update_lm_status(status)
        if abs(self._internal_cp.data.set.current - current) > 0.001:
            log.info(f"{justification}: Setting CP '{self._internal_cp_key}' charge current to {current} A (status {status})")
            self._internal_cp.data.set.current = current


    def _send_status(self):
        self._status_handler.publish_changes()
        if self._standard_socket_handler is not None:
            if  self._standard_socket_handler.get_data() is not None and self._standard_socket_handler.get_data().imported_wh is not None:
                Pub().pub(f"{yourcharge.yc_status_topic}/standard_socket", dataclasses.asdict(self._standard_socket_handler.get_data()))


    def _do_load_control(self):
        log.info(f"Regular load control NOT YET IMPLEMENTED")

        # check if control interval is actuall due
        now_it_is = datetime.datetime.utcnow()
        if (now_it_is - self._last_control_run).total_seconds() < data.data.yc_data.data.yc_config.minimum_adjustment_interval:
            log.info(f"Control loop not yet due")
            return
        self._last_control_run = now_it_is


    def _valid_ev_rfid_scanned(self, rfid_data: RfidData) -> bool:
        if rfid_data.last_tag is not None and rfid_data.last_tag != "":
            log.info(f"Detected RFID scan: {rfid_data.last_tag}: Still need to check if it's a valid EV tag ...")
            if rfid_data.last_tag in data.data.yc_data.data.yc_config.allowed_rfid_ev:
                log.info(f"!!! Detected RFID scan: {rfid_data.last_tag}: VALID EV TAG !!!")
                return True
            else:
                log.info(f"Detected RFID scan: {rfid_data.last_tag}: Is not a valid EV RFID tag")
        return False
