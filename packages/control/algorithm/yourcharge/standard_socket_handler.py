import datetime
import logging

from enum import Enum
from typing import Optional
from control import data
from control import yourcharge
from control.algorithm.yourcharge.standard_socket_meter_handler import SocketMeterData, SocketMeterHandler
from control.algorithm.yourcharge.status_handler import YcStatusHandler
from control.yourcharge import StandardSocketActions
from modules.internal_chargepoint_handler.internal_chargepoint_handler import GeneralInternalChargepointHandler
from modules.internal_chargepoint_handler.internal_chargepoint_handler_config import RfidData
from helpermodules.pub import Pub


log = logging.getLogger(__name__)


try:
    import RPi.GPIO as GPIO
except ImportError:
    log.error("failed to import RPi.GPIO! maybe we are not running on a pi")


class StandardSocketStatus(str, Enum):
    Off = "Off"
    On = "On"
    Unknown = "Unknown"


class StandardSocketControlState(int, Enum):
    Idle = 0
    ActivationRequested = 1
    DeactivationRequested = 2
    Active = 3
    WaitForEvChargeEnd = 4


class StandardSocketHandler:

    def __init__(self, general_chargepoint_handler: GeneralInternalChargepointHandler, status_handler: YcStatusHandler,
                 internal_cp_key: str) -> None:
        self._general_cp_handler = general_chargepoint_handler
        self._status_handler: YcStatusHandler = status_handler
        self._internal_cp_key: str = internal_cp_key

        self.socket_approval_max_wait_time: datetime.timedelta = datetime.timedelta(seconds=45.0)
        self.ev_charge_end_max_wait_time: datetime.timedelta = datetime.timedelta(seconds=35.0)
        self._current_status = StandardSocketStatus.Unknown
        self._current_control_state = StandardSocketControlState.Idle
        self._standard_socket_handler: Optional[SocketMeterHandler] = None
        self._previous_socket_action_for_restore = StandardSocketActions.Uninitialized
        self._last_socket_request_time = None
        self._ev_deactivation_start = None
        self._internal_cp = None
        self._init_gpio()

        # finally, for initialization, turn off the socket
        self._socket_off()

    def get_data(self) -> Optional[SocketMeterData]:
        if self._standard_socket_handler is None:
            return None
        else:
            return self._standard_socket_handler.data

    # the actual state machine handling socket activation/deactivation
    def handle_socket_algorithm(self, rfid_data: RfidData) -> bool:
        yc_control = data.data.yc_data.data.yc_control

        if not self._verify_standard_socket_presence():
            # if no socket is installed, just return
            return False

        self._internal_cp = data.data.cp_data[self._internal_cp_key]

        # now the actual statemachine
        valid_tag_seen = self.valid_socket_rfid_scanned(rfid_data)
        log.info(f"Current socket control state '{self._current_control_state.name}'")
        if self._current_control_state == StandardSocketControlState.Idle:
            self._check_idle_transitions(valid_tag_seen)
        elif self._current_control_state == StandardSocketControlState.WaitForEvChargeEnd:
            self._check_wait_for_charge_end_transitions(valid_tag_seen)
        elif self._current_control_state == StandardSocketControlState.ActivationRequested:
            self._check_activation_requested_transitions(valid_tag_seen)
        elif self._current_control_state == StandardSocketControlState.DeactivationRequested:
            self._check_deactivation_requested_transitions(valid_tag_seen)
        elif self._current_control_state == StandardSocketControlState.Active:
            self._check_socket_active_transitions(valid_tag_seen)
        else:
            log.critical(f"Unknown state '{self._current_control_state.name}': "
                         + "Turning off socket and resetting to Idle")
            self._socket_off()
            self._current_control_state = StandardSocketControlState.Idle

        # finally update approved status and return whether we've seen a valid socker RFID tag
        self._status_handler.update_socket_approved(
            yc_control.standard_socket_action == StandardSocketActions.Approve)
        return valid_tag_seen

    # gets the current status of the standard socket
    def current_socket_status(self) -> StandardSocketStatus:
        return self._current_status

    # returns a value indicating whether the EV could charge from standard socket control perspective
    def can_ev_charge(self) -> bool:
        return self._current_control_state == StandardSocketControlState.Idle

    # requests restore of the very last "pervious" state (mainly to be used when heartbeat returns)
    def restore_previous(self) -> None:
        yc_control = data.data.yc_data.data.yc_control
        if self._previous_socket_action_for_restore == StandardSocketStatus.Off:
            self._socket_off()
        elif self._previous_socket_action_for_restore == StandardSocketStatus.On \
                and yc_control.standard_socket_action == StandardSocketActions.Approve:
            self._socket_on()

    # turn off the socket (only use from outside in case of "emergency" e.g. heartbeat timeout)
    def socket_off(self) -> None:
        if self._current_control_state != StandardSocketControlState.Idle:
            self._transit_to_socket_disable_requested()

    # returns True if there's any RFID tag in the passed rfid_data and that tag is among the list of valid
    # standard-socket RFID tags
    def valid_socket_rfid_scanned(self, rfid_info: RfidData) -> bool:
        if rfid_info.last_tag is not None and rfid_info.last_tag != "":
            log.debug(f"Detected RFID scan: {rfid_info.last_tag}: Still need to check if it's a valid standard-socket "
                      + "tag ...")
            if rfid_info.last_tag in data.data.yc_data.data.yc_config.allowed_rfid_std_socket:
                log.error(f"!!! Detected RFID scan: {rfid_info.last_tag}: VALID SOCKET TAG !!!")
                return True
            else:
                log.info(f"Detected RFID scan: {rfid_info.last_tag}: Is not a valid standard-socket RFID tag")
        return False

    # transitions from Idle mode
    def _check_idle_transitions(self, valid_tag_seen: bool) -> None:
        yc_control = data.data.yc_data.data.yc_control
        if yc_control.standard_socket_action == StandardSocketActions.Approve and yc_control.socket_activated:
            log.critical("Socket marked 'active' and controller still approves socket request while in idle (maybe just"
                         + " wallbox just started): Turning on socket")
            self._transit_to_socket_on()
            return
        if valid_tag_seen:
            if self._internal_cp.data.get.charge_state:
                log.critical("Socket activation requestd by RFID scan but EV is still charging: Waiting for EV to "
                             + "finally stop charging")
                self._transit_to_wait_for_ev_charge_end()
            else:
                log.critical("Socket activation requestd by RFID scan and EV is not charging: Requesting socket "
                             + "activation right away")
                self._transit_to_socket_requested()

    # transitions from ActivationRequested mode
    def _check_activation_requested_transitions(self, valid_tag_seen: bool) -> None:
        yc_control = data.data.yc_data.data.yc_control
        if yc_control.standard_socket_action == StandardSocketActions.Approve:
            log.error("Controller approved socket request after "
                      + f"{datetime.datetime.now(datetime.timezone.utc) - self._last_socket_request_time}: Turning on socket")
            self._transit_to_socket_on()
        elif yc_control.standard_socket_action == StandardSocketActions.Decline:
            log.error(f"Controller explicitly DECLINED: Changing to {StandardSocketControlState.Idle} w/o turning on "
                      + "socket")
            self._transit_to_idle()
        elif datetime.datetime.now(datetime.timezone.utc) - self._last_socket_request_time >= self.socket_approval_max_wait_time:
            log.critical(f"No controller response after {self.socket_approval_max_wait_time} on standard socket "
                         + f"activation request at {self._last_socket_request_time}: No longer waiting, reverting to "
                         + f"{StandardSocketControlState.Idle}")
            self._transit_to_idle()

    # transitions from DeactivationRequested mode
    def _check_deactivation_requested_transitions(self, valid_tag_seen: bool) -> None:
        yc_control = data.data.yc_data.data.yc_control
        if yc_control.standard_socket_action != StandardSocketActions.Approve:
            log.error("Controller disapproved socket request after "
                      + f"{datetime.datetime.now(datetime.timezone.utc) - self._last_socket_request_time}: Turning off socket")
            self._transit_to_idle()
        elif datetime.datetime.now(datetime.timezone.utc) - self._last_socket_request_time >= self.socket_approval_max_wait_time:
            log.critical(f"No controller response after {self.socket_approval_max_wait_time} on standard socket "
                         + f"activation request at {self._last_socket_request_time}: No longer waiting, reverting to "
                         + f"{StandardSocketControlState.Idle}")
            self._transit_to_idle()

    # transitions from Active mode
    def _check_socket_active_transitions(self, valid_tag_seen: bool) -> None:
        yc_control = data.data.yc_data.data.yc_control
        if valid_tag_seen:
            log.error("De-activation requested by RFID-tag: Turning off socket and changing to "
                      + f"{StandardSocketControlState.Idle}")
            self._transit_to_socket_disable_requested()
        elif yc_control.standard_socket_action != StandardSocketActions.Approve:
            log.error("Controller no longer approves standard-socket: Turning off socket and changing to "
                      + f"{StandardSocketControlState.Idle}")
            self._transit_to_idle()

    # transitions from wait-for-EV-charge-end mode
    def _check_wait_for_charge_end_transitions(self, valid_tag_seen: bool) -> None:
        if valid_tag_seen:
            log.error("De-activation requested by RFID-tag while waiting for EV charge end: Turning off socket and "
                      + f"changing to {StandardSocketControlState.Idle}")
            self._transit_to_socket_disable_requested()
            return

        if self._internal_cp.data.get.charge_state:
            log.error("EV still charging while waiting for charge end. Waiting started at "
                      + f"{self._ev_deactivation_start}")
            if self._ev_deactivation_start is not None \
                    and (datetime.datetime.now(datetime.timezone.utc) - self._ev_deactivation_start) \
                    > self.ev_charge_end_max_wait_time:
                log.error("Timeout waiting for EV charge end: Switching to idle. Waiting started at "
                          + f"{self._ev_deactivation_start}, waiting for "
                          + f"{datetime.datetime.now(datetime.UTC) - self._ev_deactivation_start}")
                self._transit_to_idle()
        else:
            log.error("EV stopped charging when waiting for charge end")
            self._ev_deactivation_start = None
            self._transit_to_socket_requested()

    # turn off the socket (only to be used internally)
    def _socket_off(self) -> None:
        if self._current_status == StandardSocketStatus.Off:
            return
        self._previous_socket_action_for_restore = self._current_status
        self._gpio_off()
        self._current_control_state = StandardSocketControlState.Idle

    def _gpio_off(self) -> None:
        GPIO.output(15, GPIO.HIGH)
        self._current_status = StandardSocketStatus.Off
        Pub().pub(yourcharge.yc_socket_activated_topic, self._current_status == StandardSocketStatus.On)

    # turn on the socket (only to be used internally)
    def _socket_on(self) -> None:
        if self._current_status == StandardSocketStatus.On:
            return
        self._previous_socket_action_for_restore = self._current_status
        self._gpio_on()

    def _gpio_on(self) -> None:
        GPIO.output(15, GPIO.LOW)
        self._current_status = StandardSocketStatus.On
        Pub().pub(yourcharge.yc_socket_activated_topic, self._current_status == StandardSocketStatus.On)

    # transition action when waiting for EV charge end
    def _transit_to_wait_for_ev_charge_end(self) -> None:
        self._ev_deactivation_start = datetime.datetime.now(datetime.timezone.utc)
        self._current_control_state = StandardSocketControlState.WaitForEvChargeEnd
        log.error(f"Socket requested by EV still charging: Waiting for EV charge end at {self._ev_deactivation_start}")

    # transition action when requesting ENABLE of socket
    def _transit_to_socket_requested(self) -> None:
        if self._current_control_state == StandardSocketControlState.ActivationRequested:
            return
        self._current_control_state = StandardSocketControlState.ActivationRequested
        self._last_socket_request_time = datetime.datetime.now(datetime.timezone.utc)
        log.error(f"Requesting activation of standard socket at {self._last_socket_request_time} by sending "
                  + f"{yourcharge.SocketRequestStates.OnRequested}")
        Pub().pub(yourcharge.yc_socket_requested_topic, yourcharge.SocketRequestStates.OnRequested)

    # transition action when requesting DISABLE of socket
    def _transit_to_socket_disable_requested(self) -> None:
        if self._current_control_state == StandardSocketControlState.DeactivationRequested:
            return
        self._current_control_state = StandardSocketControlState.DeactivationRequested
        self._last_socket_request_time = datetime.datetime.now(datetime.timezone.utc)
        self._ev_deactivation_start = None
        log.error(f"Requesting deactivation of standard socket at {self._last_socket_request_time} by sending "
                  + f"{yourcharge.SocketRequestStates.OffRequested}")
        Pub().pub(yourcharge.yc_socket_requested_topic, yourcharge.SocketRequestStates.OffRequested)

        # following is not needed as socket would get turned off anyway when controller disapproves due to OffRequested
        # above but this way, user in front of wallbox gets more direct "feedback"
        self._gpio_off()

    # transition action when returning to idle
    def _transit_to_socket_on(self) -> None:
        if self._current_control_state == StandardSocketControlState.Active:
            return
        self._current_control_state = StandardSocketControlState.Active
        self._last_socket_request_time = None
        self._ev_deactivation_start = None
        self._socket_on()
        Pub().pub(yourcharge.yc_socket_requested_topic, yourcharge.SocketRequestStates.NoRequest)

    # transition action when returning to idle
    def _transit_to_idle(self) -> None:
        if self._current_control_state == StandardSocketControlState.Idle:
            return
        self._current_control_state = StandardSocketControlState.Idle
        self._last_socket_request_time = None
        self._ev_deactivation_start = None
        log.error(f"Standard socket returning to {StandardSocketControlState.Idle}")
        self._socket_off()
        Pub().pub(yourcharge.yc_socket_requested_topic, yourcharge.SocketRequestStates.NoRequest)

    # en/disable standard socket handler on internal CP handler as configured by YC config
    # then return true if standard socket is present, otherwise false
    def _verify_standard_socket_presence(self) -> bool:
        if data.data.yc_data.data.yc_config.standard_socket_installed is not None \
                and data.data.yc_data.data.yc_config.standard_socket_installed:
            if self._standard_socket_handler is None:
                self._standard_socket_handler = SocketMeterHandler(
                    self._general_cp_handler.internal_chargepoint_handler.cp0_client_handler.client)
            if self._general_cp_handler.internal_chargepoint_handler is not None:
                self._general_cp_handler.internal_chargepoint_handler.standard_socket_meter_handler = \
                    self._standard_socket_handler
            log.info(f"Standard-Socket data: {self._standard_socket_handler.data}")
            return True
        else:
            if self._standard_socket_handler is not None:
                self._standard_socket_handler = None
            if self._general_cp_handler.internal_chargepoint_handler is not None:
                self._general_cp_handler.internal_chargepoint_handler.standard_socket_meter_handler = None
            # reset the SM state and socket status for non-present socket
            self._current_status = StandardSocketStatus.Unknown
            self._current_control_state = StandardSocketControlState.Idle
            return False

    def _init_gpio(self) -> None:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(15, GPIO.OUT)
