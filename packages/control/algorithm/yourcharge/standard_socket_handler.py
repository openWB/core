import datetime
import logging

from enum import Enum
from control import data
from control import yourcharge
from control.algorithm.yourcharge.standard_socket_meter_handler import SocketMeterData, SocketMeterHandler
from control.yourcharge import StandardSocketActions
from modules.internal_chargepoint_handler.internal_chargepoint_handler import GeneralInternalChargepointHandler
from modules.internal_chargepoint_handler.internal_chargepoint_handler_config import RfidData
from helpermodules.pub import Pub


log = logging.getLogger(__name__)


try:
    import RPi.GPIO as GPIO
except ImportError:
    log.info("failed to import RPi.GPIO! maybe we are not running on a pi")


class StandardSocketStatus(str, Enum):
    Off = "Off"
    On = "On"
    Unknown = "Unknown"


class StandardSocketControlState(int, Enum):
    Idle = 0
    ActivationRequested = 1
    Active = 3


class StandardSocketHandler:

    def __init__(self, general_chargepoint_handler: GeneralInternalChargepointHandler) -> None:
        self.__general_cp_handler = general_chargepoint_handler

        self.socket_approval_max_wait_time: datetime.timedelta = datetime.timedelta(seconds=45.0)
        self.__current_status = StandardSocketStatus.Unknown
        self.__current_control_state = StandardSocketControlState.Idle
        self.__standard_socket_handler: SocketMeterHandler = None
        self.__previous_socket_action_for_restore = StandardSocketActions.Uninitialized
        self.__last_socket_request_time = None
        self.__init_gpio()

        # finally, for initialization, turn off the socket
        self.socket_off()


    def get_data(self) -> SocketMeterData:
        if self.__standard_socket_handler is None:
            return None
        else:
            return self.__standard_socket_handler.data


    # the actual state machine handling socket activation/deactivation
    def handle_socket_algorithm(self, rfid_data: RfidData) -> None:
        if not self.__verify_standard_socket_presence():
            # if no socket is installed, just return
            return

        # now the actual statemachine
        log.info(f"Current socket control state '{self.__current_control_state.name}'")
        if self.__current_control_state ==  StandardSocketControlState.Idle:
            self.__check_idle_transitions(rfid_data)
        elif self.__current_control_state ==  StandardSocketControlState.ActivationRequested:
            self.__check_activation_requested_transitions(rfid_data)
        elif self.__current_control_state ==  StandardSocketControlState.Active:
            self.__check_socket_active_transitions(rfid_data)
        else:
            log.critical(f"Unknown state '{self.__current_control_state.name}': Turning off socket and resetting to Idle")
            self.socket_off()
            self.__current_control_state = StandardSocketControlState.Idle


    # gets the current status of the standard socket
    def current_socket_status(self) -> StandardSocketStatus:
        return self.__current_status


    # returns a value indicating whether the EV could charge from standard socket control perspective
    def can_ev_charge(self) -> bool:
        return self.__current_control_state == StandardSocketControlState.Idle


    # requests restore of the very last "pervious" state (mainly to be used when heartbeat returns)
    def restore_previous(self) -> None:
        if self.__previous_socket_action_for_restore == StandardSocketStatus.Off:
            self.socket_off()
        elif self.__previous_socket_action_for_restore == StandardSocketStatus.On and data.data.yc_data.data.yc_control.standard_socket_action == StandardSocketActions.Approve:
            self.socket_on()


    # turn off the socket (only use from outside in case of "emergency" e.g. heartbeat timeout)
    def socket_off(self) -> None:
        if self.__current_status == StandardSocketStatus.Off:
            return
        self.__previous_socket_action_for_restore = self.__current_status
        GPIO.output(15, GPIO.HIGH)
        self.__current_status = StandardSocketStatus.Off
        self.__current_control_state = StandardSocketControlState.Idle
        Pub().pub(yourcharge.yc_socket_activated_topic, self.__current_status == StandardSocketStatus.On)


    # returns True if there's any RFID tag in the passed rfid_data and that tag is among the list of valid standard-socket RFID tags
    def valid_socket_rfid_scanned(self, rfid_data: RfidData) -> bool:
        if rfid_data.last_tag is not None and rfid_data.last_tag != "":
            log.info(f"Detected RFID scan: {rfid_data.last_tag}: Still need to check if it's a valid tag ...")
            if rfid_data.last_tag in data.data.yc_data.data.yc_config.allowed_rfid_std_socket:
                log.info(f"!!! Detected RFID scan: {rfid_data.last_tag}: VALID SOCKET TAG !!!")
                return True
            else:
                log.info(f"Detected RFID scan: {rfid_data.last_tag}: Is not a valid standard-socket RFID tag")
        return False


    # transitions from Idle mode
    def __check_idle_transitions(self, rfid_data: RfidData) -> None:
        if self.valid_socket_rfid_scanned(rfid_data):
            self.__transit_to_socket_requested()


    # transitions from ActivationRequested mode
    def __check_activation_requested_transitions(self, rfid_data: RfidData) -> None:
        if data.data.yc_data.data.yc_control.standard_socket_action == StandardSocketActions.Approve:
            log.critical(f"Controller approved socket request after {datetime.datetime.utcnow() - self.__last_socket_request_time}: Turning on socket")
            self.__transit_to_socket_on()
        elif data.data.yc_data.data.yc_control.standard_socket_action == StandardSocketActions.Decline:
            log.critical(f"Controller explicitly DECLINED: Changing to {StandardSocketControlState.Idle} w/o turning on socket")
            self.__transit_to_idle()
        elif datetime.datetime.utcnow() - self.__last_socket_request_time >= self.socket_approval_max_wait_time:
            log.critical(f"No controller response after {self.socket_approval_max_wait_time} on standard socket activation request at {self.__last_socket_request_time}: No longer waiting, reverting to {StandardSocketControlState.Idle}")
            self.__transit_to_idle()


    # transitions from Active mode
    def __check_socket_active_transitions(self, rfid_data: RfidData) -> None:
        if self.valid_socket_rfid_scanned(rfid_data):
            log.critical(f"De-activation requested by RFID-tag: Turning off socket and changing to {StandardSocketControlState.Idle}")
            self.__transit_to_idle()
        elif data.data.yc_data.data.yc_control.standard_socket_action != StandardSocketActions.Approve:
            log.critical(f"Controller no longer approves standard-socket: Turning off socket and changing to {StandardSocketControlState.Idle}")
            self.__transit_to_idle()


    # turn on the socket (only to be used internally)
    def __socket_on(self) -> None:
        if self.__current_status == StandardSocketStatus.On:
            return
        self.__previous_socket_action_for_restore = self.__current_status
        GPIO.output(15, GPIO.LOW)
        self.__current_status = StandardSocketStatus.On
        Pub().pub(yourcharge.yc_socket_activated_topic, self.__current_status == StandardSocketStatus.On)


    # transition action when requesting socket
    def __transit_to_socket_requested(self) -> None:
        if self.__current_control_state == StandardSocketControlState.ActivationRequested:
            return
        self.__current_control_state = StandardSocketControlState.ActivationRequested
        self.__last_socket_request_time = datetime.datetime.utcnow()
        log.info(f"Requesting activation of standard socket at {self.__last_socket_request_time} by sending {yourcharge.SocketRequestStates.OnRequested}")
        Pub().pub(yourcharge.yc_socket_requested_topic, yourcharge.SocketRequestStates.OnRequested)


    # transition action when returning to idle
    def __transit_to_socket_on(self) -> None:
        if self.__current_control_state == StandardSocketControlState.Active:
            return
        self.__current_control_state = StandardSocketControlState.Active
        self.__last_socket_request_time = None
        self.__socket_on()
        Pub().pub(yourcharge.yc_socket_requested_topic, yourcharge.SocketRequestStates.NoRequest)


    # transition action when returning to idle
    def __transit_to_idle(self) -> None:
        if self.__current_control_state == StandardSocketControlState.Idle:
            return
        self.__current_control_state = StandardSocketControlState.Idle
        self.__last_socket_request_time = None
        log.info(f"Standard socket returning to {StandardSocketControlState.Idle}")
        self.socket_off()
        Pub().pub(yourcharge.yc_socket_requested_topic, yourcharge.SocketRequestStates.NoRequest)


    # en/disable standard socket handler on internal CP handler as configured by YC config
    # then return true if standard socket is present, otherwise false
    def __verify_standard_socket_presence(self) -> bool:
        if data.data.yc_data.data.yc_config.standard_socket_installed:
            if self.__standard_socket_handler == None:
                self.__standard_socket_handler = SocketMeterHandler(self.__general_cp_handler.internal_chargepoint_handler.cp0_client_handler.client)
            if self.__general_cp_handler.internal_chargepoint_handler.cp0.module.standard_socket_handler is None:
                self.__general_cp_handler.internal_chargepoint_handler.cp0.module.standard_socket_handler = self.__standard_socket_handler
            log.info(f"Standard-Socket data: {self.__standard_socket_handler.data}")
            return True
        else:
            if self.__standard_socket_handler != None:
                self.__standard_socket_handler = None
            if self.__general_cp_handler.internal_chargepoint_handler.cp0.module.standard_socket_handler is not None:
                self.__general_cp_handler.internal_chargepoint_handler.cp0.module.standard_socket_handler = None
            # reset the SM state and socket status for non-present socket
            self.__current_status = StandardSocketStatus.Unknown
            self.__current_control_state = StandardSocketControlState.Idle
            return False


    def __init_gpio(self) -> None:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(15, GPIO.OUT)
