import datetime
import logging
import dataclasses

from enum import Enum
from datetime import timedelta

from control import data, yourcharge
from control.algorithm.yourcharge.control_algorithm_yc import ControlAlgorithmYc
from control.algorithm.yourcharge.heartbeat_checker import HeartbeatChecker
from control.algorithm.yourcharge.standard_socket_handler import StandardSocketHandler
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


class StatemachineYc():

    def __init__(self, general_chargepoint_handler: GeneralInternalChargepointHandler):
        (key, value) = next(((key, value) for i, (key, value) in enumerate(data.data.cp_data.items())
                            if value.chargepoint_module.config.type == 'internal_openwb'), None)
        self._status_handler: YcStatusHandler = YcStatusHandler()
        self._internal_cp = value
        self._internal_cp_key = key
        self._wait_for_socket_idle = False
        self._last_rfid_data = None
        self._rfiddata_for_ev_activation = None
        self._valid_standard_socket_tag_found = False
        self._general_cp_handler = general_chargepoint_handler
        self._heartbeat_checker: HeartbeatChecker = HeartbeatChecker(timedelta(seconds=25))
        self._standard_socket_handler: StandardSocketHandler = StandardSocketHandler(
            general_chargepoint_handler,
            self._status_handler, key)
        self._current_control_state = LoadControlState.Startup
        self._wait_for_plugin_entered = None
        self._control_algorithm = ControlAlgorithmYc(key, self._status_handler)
        self._previous_plug_state = None
        self._previous_justification = None
        self._last_data_update_timestamp = datetime.datetime(1, 1, 2, 0, 0, 0, tzinfo=datetime.timezone.utc)
        self._data_update_interval = timedelta(seconds=30)
        self._justification = ""
        self._current = 0.0
        self._status = yourcharge.LmStatus.DownByError
        log.error(f"YC algorithm active: Internal CP found as '{self._internal_cp_key}'")

    def perform_load_control(self) -> None:

        try:
            # (key, value) = next(((key, value) for i, (key, value) in enumerate(data.data.cp_data.items())
            # if value.chargepoint_module.config.type == 'internal_openwb'), None)
            self._internal_cp = data.data.cp_data[self._internal_cp_key]
            now_it_is = datetime.datetime.now(datetime.timezone.utc)
            # log.error(f"Internal CP now '{id(self._internal_cp)}'")

            # check heartbeat and super-early exit in case of controller not being seen anymore, charge current --> 0
            # and socket --> off
            self._status_handler.update_heartbeat_ok(self._heartbeat_checker.is_heartbeat_ok())

            # copy cp-enabled state from control (and persistence) area to current status (which gets used subsequently)
            # current status implictly updates control when changed
            # this way the cp-enabled status gets persisted in MQTT server
            self._status_handler.update_cp_enabled(data.data.yc_data.data.yc_control.cp_enabled)

            # signal the received energy limit in status so controller can check what is currently configured
            self._status_handler.update_energy_limit(data.data.yc_data.data.yc_config.energy_limit)

            # get data that we need
            self._last_rfid_data = SubData.internal_chargepoint_data["rfid_data"]
            if self._last_rfid_data is not None and self._last_rfid_data.last_tag != "":
                self._rfiddata_for_ev_activation = self._last_rfid_data
                self._status_handler.update_rfid_scan(rfid=self._last_rfid_data.last_tag, timestamp=now_it_is)
                self._valid_standard_socket_tag_found = \
                    self._standard_socket_handler.valid_socket_rfid_scanned(self._last_rfid_data)
                if (self._valid_standard_socket_tag_found):
                    self._unlock_display()
                else:
                    self._valid_ev_rfid_scanned(self._last_rfid_data)
            else:
                self._valid_standard_socket_tag_found = False

            # detect plugin (for accounting and engery since plugged)
            plugin = False
            plugout = False
            if self._previous_plug_state is None:
                self._status_handler.get_accounting()
            elif not self._previous_plug_state and self._internal_cp.data.get.plug_state:
                # transition from unplugged -> plugged -> update meter value at plugin
                plugin = True
                self._status_handler.update_cp_meter_at_last_plugin(self._internal_cp.data.get.imported)
            elif self._previous_plug_state and not self._internal_cp.data.get.plug_state:
                # transition from plugged -> unplugged
                plugout = True

            # calculate charged-since-plugged and charged-today
            cp_meter_at_last_plugin = self._status_handler.get_cp_meter_at_last_plugin()
            if cp_meter_at_last_plugin is not None:
                self._status_handler.update_energy_charged_since_last_plugin(
                    self._internal_cp.data.get.imported - cp_meter_at_last_plugin)

            log.debug(f"---> Entering with load control state {self._current_control_state.name}, last RFID data "
                      + f"{self._last_rfid_data}, valid standard socket tag {self._valid_standard_socket_tag_found}")

            # globally handle superseded (we have to obey at first - transitions may overwrite it)
            if data.data.yc_data.data.yc_control.fixed_charge_current is not None \
                    and data.data.yc_data.data.yc_control.fixed_charge_current >= 0:
                self._set_current("Fixed current requested by yc_data.data.yc_control.fixed_charge_current",
                                  data.data.yc_data.data.yc_control.fixed_charge_current,
                                  yourcharge.LmStatus.Superseded)

            if not self._status_handler.get_heartbeat_ok():
                # unconditional early exit in case of heartbeat timeout: charge current --> 0 and socket --> off
                self._transition_to_heartbeat_timeout()
            elif not data.data.yc_data.data.yc_config.active:
                # unconditional early exit in case of box being administratively disabled: charge current --> 0
                # and socket --> off
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
                log.error(f"Unknown state '{self._current_control_state.name}': Resetting to Idle")
                self._current_control_state = LoadControlState.Idle

            log.debug(f"Leaving with load control state {self._current_control_state.name}")

        finally:
            self._execute_set_current()
            self._valid_standard_socket_tag_found = False
            self._previous_plug_state = self._internal_cp.data.get.plug_state

            # handle slow data update
            if plugin or plugout or (now_it_is - self._last_data_update_timestamp >= self._data_update_interval):
                self._last_data_update_timestamp = now_it_is
                self._status_handler.update_energy_charged_today(self._internal_cp.data.get.imported)
                if plugin or self._internal_cp.data.get.plug_state:
                    self._status_handler.update_accounting(now_it_is, self._internal_cp.data.get.imported,
                                                           self._internal_cp.data.get.charge_state,
                                                           self._internal_cp.data.get.plug_state)

            self._send_status()
            SubData.internal_chargepoint_data["rfid_data"].last_tag = ""

    # ### transition checks ###
    def _check_idle_transitions(self) -> None:
        # first check for socket activation
        if self._check_transition_for_standard_socket():
            return

        if self._valid_ev_rfid_scanned(self._last_rfid_data):
            self._status_handler.update_cp_enabled(True)
            if self._internal_cp.data.get.plug_state:
                if self._rfiddata_for_ev_activation is not None:
                    meter_value_to_use = self._status_handler.get_cp_meter_at_last_plugin()
                    if meter_value_to_use is None:
                        meter_value_to_use = self._internal_cp.data.get.imported
                    self._status_handler.new_accounting(datetime.datetime.now(datetime.timezone.utc),
                                                        meter_value_to_use,
                                                        self._internal_cp.data.get.charge_state,
                                                        self._internal_cp.data.get.plug_state,
                                                        self._rfiddata_for_ev_activation.last_tag)
                    self._rfiddata_for_ev_activation = None
                else:
                    log.error("Internal error: Detected valid RFID scan but _rfiddata_for_ev_activation is still None")
                self._state_change("Valid EV RFID tag scanned while idle but plugged-in", LoadControlState.EvActive)
            else:
                self._wait_for_plugin_entered = datetime.datetime.now(datetime.timezone.utc)
                self._state_change("Valid EV RFID tag scanned while idle and unplugged: Waiting "
                                   + f"{data.data.yc_data.data.yc_config.max_plugin_wait_time_s} for plugin",
                                   LoadControlState.WaitingForPlugin)

    def _check_wait_for_plugin_transitions(self) -> None:
        # first check for socket activation
        if self._check_transition_for_standard_socket():
            self._wait_for_plugin_entered = None
            self._state_change("Detected standard socket activation while waiting for plugin: "
                               + "Terminating wait for plugin", LoadControlState.SocketActive)
            return

        if not self._status_handler.get_cp_enabled():
            self._wait_for_plugin_entered = None
            self._state_change("Chargepoint got disabled from outside while waiting for plugin", LoadControlState.Idle)

        if self._internal_cp.data.get.plug_state:
            self._wait_for_plugin_entered = None
            if self._rfiddata_for_ev_activation is not None:
                self._status_handler.new_accounting(datetime.datetime.now(datetime.timezone.utc),
                                                    self._status_handler.get_cp_meter_at_last_plugin(),
                                                    self._internal_cp.data.get.charge_state,
                                                    self._internal_cp.data.get.plug_state,
                                                    self._rfiddata_for_ev_activation.last_tag)
                self._rfiddata_for_ev_activation = None
            else:
                log.error("Internal error: Plugin while waiting for it but _rfiddata_for_ev_activation is still None")
            self._state_change("Detected plugin while waiting for plugin", LoadControlState.EvActive)

        # then check for expired wait time
        if self._wait_for_plugin_entered is None:
            self._wait_for_plugin_entered = datetime.datetime.now(datetime.timezone.utc)
        else:
            elapsed = datetime.datetime.now(datetime.timezone.utc) - self._wait_for_plugin_entered
            if elapsed.total_seconds() >= data.data.yc_data.data.yc_config.max_plugin_wait_time_s:
                self._wait_for_plugin_entered = None
                self._status_handler.update_cp_enabled(False)
                self._state_change(f"Waiting for plugin timed out after {elapsed.total_seconds()} s",
                                   LoadControlState.Idle, logging.WARNING)

    def _check_socket_active_transitions(self) -> None:
        if self._valid_standard_socket_tag_found:
            log.error("Detected socket RFID scan while socket is active: Starting turn-off procedure")
            self._standard_socket_handler.socket_off()
            self._wait_for_socket_idle = True
            # no transition yet - only transit once EV can charge is signaled again
            return

        # first check for EV activation or "re-scan" of socket RFID tag -> in both cases we trigger disable
        # of standard socket
        if self._valid_ev_rfid_scanned(self._last_rfid_data):
            log.error("Detected EV RFID scan while socket is active: Starting turn-off procedure")
            self._standard_socket_handler.socket_off()
            self._wait_for_socket_idle = True
            # no transition yet - only transit once EV can charge is signaled again
            return

        if self._wait_for_socket_idle:
            if not self._check_transition_for_standard_socket():
                self._wait_for_socket_idle = False
                self._state_change("Standard socket now off", self._derive_state())
        else:
            # after one iteration of socket handler the can_ev_charge should reflect actual the handler state
            self._wait_for_socket_idle = True

    def _check_transition_for_standard_socket(self) -> bool:
        if self._standard_socket_handler.handle_socket_algorithm(self._last_rfid_data):
            if self._standard_socket_handler.can_ev_charge():
                return False
            else:
                self._transition_to_standard_socket()
                return True
        else:
            return False

    def _check_ev_active_transitions(self) -> None:
        if self._valid_standard_socket_tag_found:
            self._transition_to_standard_socket()
            return

        if not self._internal_cp.data.get.plug_state:
            self._status_handler.update_cp_enabled(False)
            self._status_handler.end_accounting(datetime.datetime.now(datetime.timezone.utc), self._internal_cp.data.get.imported)
            self._set_current("Detected unplug while in EV charge", 0.0, yourcharge.LmStatus.DownByDisable)
            self._state_change("Detected unplug while in EV charge", LoadControlState.Idle)
            return

        if not self._status_handler.get_cp_enabled():
            self._set_current(
                "Chargepoint got disabled from outside while in regular control loop",
                0.0,
                yourcharge.LmStatus.DownByDisable)
            self._state_change("Chargepoint got disabled from outside while in regular control loop",
                               LoadControlState.Idle)

        self._set_current("Regular control loop", -1, yourcharge.LmStatus.InLoop)
        self._control_algorithm.do_load_control()

    def _check_disabled_transitions(self) -> None:
        # handle re-activation
        if data.data.yc_data.data.yc_config.active:
            self._standard_socket_handler.restore_previous()
            self._state_change("Box was administratively re-activated: Trying to restore previous state",
                               LoadControlState.Idle)

    def _check_startup_transitions(self) -> None:
        self._status_handler.update_rfid_scan(None, datetime.datetime.now(datetime.timezone.utc))
        self._standard_socket_handler.restore_previous()
        self._state_change("Startup", self._derive_state())
        self._set_current("Startup", 0.0, yourcharge.LmStatus.InLoop)

    def _check_heartbeat_timeout_transitions(self) -> None:
        # handle re-appearing heartbeat
        if self._status_handler.has_changed_heartbeat():
            self._standard_socket_handler.restore_previous()
            self._state_change("Controller heartbeat returned: Trying to restore previous state", self._derive_state())
            self._set_current("Re-appearing from Heartbeat timeout", 0.0, yourcharge.LmStatus.InLoop)

    # ### transition actions ###
    def _transition_to_standard_socket(self):
        # immediately disable CP when valid standard socket tag has been found
        self._status_handler.update_cp_enabled(False)
        self._set_current("Standard socket requested: Disabling charge immediately", 0.0,
                          yourcharge.LmStatus.DownForSocket)
        self._state_change("Standard socket requested", LoadControlState.SocketActive)

    def _transition_to_disabled(self):
        self._set_current("Box is administratively disabled: Disabling charge immediately", 0.0,
                          yourcharge.LmStatus.DownByDisable)
        self._standard_socket_handler._socket_off()
        self._state_change("Box is administratively disabled", LoadControlState.Disabled)

    def _transition_to_heartbeat_timeout(self):
        self._set_current("Detected controller heartbeat timeout: Disabling charge immediately", 0.0,
                          yourcharge.LmStatus.DownByError)
        self._standard_socket_handler._socket_off()
        self._state_change("Detected controller heartbeat timeout", LoadControlState.HeartbeatTimeout)

    # ### other, non-statemachine, methods
    def _set_current(self, justification: str, current: float, status: yourcharge.LmStatus):
        self._justification = justification
        self._current = current
        self._status = status

    def _execute_set_current(self):
        # self._current < 0 is indicator for "current set elsewhere"
        if self._current >= 0:
            self._control_algorithm.set_current(self._justification, self._current, self._status)

    def _send_status(self):
        self._status_handler.publish_changes()
        if self._standard_socket_handler is not None:
            if self._standard_socket_handler.get_data() is not None \
                    and self._standard_socket_handler.get_data().imported_wh is not None:
                Pub().pub(f"{yourcharge.yc_status_topic}/standard_socket",
                          dataclasses.asdict(self._standard_socket_handler.get_data()))

    def _valid_ev_rfid_scanned(self, rfid_data: RfidData) -> bool:
        if rfid_data.last_tag is not None and rfid_data.last_tag != "":
            log.error(f"Detected RFID scan: {rfid_data.last_tag}: Still need to check if it's a valid EV tag ...")
            if rfid_data.last_tag in data.data.yc_data.data.yc_config.allowed_rfid_ev:
                log.error(f"!!! Detected RFID scan: {rfid_data.last_tag}: VALID EV TAG !!!")
                self._unlock_display()
                return True
            else:
                log.error(f"Detected RFID scan: {rfid_data.last_tag}: Is not a valid EV RFID tag")
        return False

    def _unlock_display(self) -> None:
        log.error("Unlocking display")
        Pub().pub(yourcharge.yc_display_unlock_topic, False)

    def _get_state_from_plugstate(self) -> LoadControlState:
        if self._internal_cp.data.get.plug_state:
            return LoadControlState.EvActive
        else:
            return LoadControlState.WaitingForPlugin

    def _state_change(self, info_text: str, new_state: LoadControlState, log_level=logging.ERROR):
        if self._current_control_state != new_state:
            log.log(level=log_level, msg=f"---> {info_text}: Switching to state '{new_state.name}'")
            self._current_control_state = new_state
        else:
            log.debug(f"---> {info_text}: Staying in state '{new_state.name}'")

    def _derive_state(self) -> LoadControlState:
        if data.data.yc_data.data.yc_control.cp_enabled:
            if self._standard_socket_handler.can_ev_charge():
                return_state = self._get_state_from_plugstate()
            else:
                return_state = LoadControlState.SocketActive
        else:
            if self._standard_socket_handler.can_ev_charge():
                return_state = LoadControlState.Idle
            else:
                return_state = LoadControlState.SocketActive
        return return_state
