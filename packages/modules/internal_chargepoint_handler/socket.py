from enum import IntEnum
import functools
import logging
import time
from typing import Callable

from helpermodules.hardware_configuration import get_hardware_configuration_setting
from helpermodules.logger import ModifyLoglevelContext
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import ChargepointState
from modules.common.evse import EvseStatusCode
from modules.common.modbus import ModbusDataType
from modules.internal_chargepoint_handler.chargepoint_module import ChargepointModule
from modules.internal_chargepoint_handler.clients import ClientHandler
from modules.internal_chargepoint_handler.internal_chargepoint_handler_config import InternalChargepoint
from helpermodules.pub import Pub
from modules.common.connector_unlock import currents_are_zero, UNLOCK_STABLE_SECONDS, UNLOCK_TIMEOUT


log = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
except ImportError:
    log.info("failed to import RPi.GPIO! maybe we are not running on a pi")


class RateLimiter:
    def __init__(self, max_calls: int, max_seconds: int):
        self.movement_times = [0.0]*max_calls
        self.max_seconds = max_seconds
        self.counter = 0

    def __call__(self, delegate: Callable):
        @functools.wraps(delegate)
        def wrapper(*args, **kwargs):
            now = time.time()
            sleep_needed = self.max_seconds - (now - self.movement_times[self.counter])
            if sleep_needed > 0:
                log.debug("Actor cool down. Not moving actor.")
                return None
            else:
                self.movement_times[self.counter] = time.time()
                self.counter = (self.counter + 1) % len(self.movement_times)
                return delegate(*args, **kwargs)
        return wrapper


class ActorState(IntEnum):
    CLOSED = 0,
    OPENED = 1


class Socket(ChargepointModule):
    def __init__(self,
                 local_charge_point_num: int,
                 client_handler: ClientHandler,
                 internal_cp: InternalChargepoint,
                 hierarchy_id: int) -> None:
        self.socket_max_current = get_hardware_configuration_setting("max_c_socket")
        with ModifyLoglevelContext(log, logging.DEBUG):
            log.info(f"Konfiguration als Buchse mit maximal {self.socket_max_current}A Ladestrom je Phase.")
        super().__init__(local_charge_point_num, client_handler, internal_cp, hierarchy_id)
        self._unlock_blocked = internal_cp.get.unlock_blocked

    @property
    def unlock_blocked(self) -> bool:
        return self._unlock_blocked

    def _set_unlock_blocked(self, blocked: bool) -> None:
        self._unlock_blocked = blocked
        Pub().pub(f"openWB/set/internal_chargepoint/{self.local_charge_point_num}/get/unlock_blocked", blocked)

    def _read_unlock_state(self):
        # Bypass get_values(): its cached/zero fallback values cannot authorize release.
        with self._client.client:
            self._client.evse_client.set_current(0)
            evse, meter = self._client.request_and_check_hardware(self.fault_state)
            controller = self._client.evse_client
            raw_current, _, state = controller.client.read_holding_registers(
                1000, [ModbusDataType.UINT_16]*3, unit=controller.id)
        safe = (raw_current == 0 and state in (EvseStatusCode.READY, EvseStatusCode.EV_PRESENT)
                and evse.charge_state is False and evse.set_current == 0 and currents_are_zero(meter.currents))
        return evse.plug_state, safe

    def perform_unlock(self, timeout: float = UNLOCK_TIMEOUT, cancelled=None) -> bool:
        """Run only in the hardware handler, with phase/CP operations excluded."""
        self._set_unlock_blocked(True)
        deadline = time.monotonic() + min(max(timeout, 0), UNLOCK_TIMEOUT)
        stable_since = None
        while time.monotonic() < deadline and not (cancelled and cancelled.is_set()):
            _, safe = self._read_unlock_state()
            now = time.monotonic()
            if now >= deadline or (cancelled and cancelled.is_set()):
                break
            if not safe:
                stable_since = None
            elif stable_since is None:
                stable_since = now
            if stable_since is not None and now - stable_since >= UNLOCK_STABLE_SECONDS:
                if ActorState(GPIO.input(19)) != ActorState.OPENED:
                    self.__open_actor()
                return ActorState(GPIO.input(19)) == ActorState.OPENED
            time.sleep(0.5)
        return False

    def set_current(self, current: float) -> None:
        if self._unlock_blocked:
            super().set_current(0)
            return
        with SingleComponentUpdateContext(self.fault_state, update_always=False):
            with self.client_error_context:
                actor = ActorState(GPIO.input(19))

                if actor == ActorState.OPENED:
                    current = 0
                super().set_current(min(current, self.socket_max_current))
                if actor == ActorState.OPENED and self.chargepoint_state.plug_state is True:
                    raise ValueError("Buchse hat nicht verriegelt, obwohl ein Fahrzeug angesteckt ist.")

    def get_values(self, phase_switch_cp_active: bool, last_tag: str) -> ChargepointState:
        with self.client_error_context:
            actor = ActorState(GPIO.input(19))
            log.debug("Actor: "+str(actor))
            self.chargepoint_state = super().get_values(phase_switch_cp_active, last_tag)
            self.chargepoint_state.max_evse_current = self.socket_max_current
            if self._unlock_blocked:
                if not phase_switch_cp_active:
                    plugged, safe = self._read_unlock_state()
                    if plugged is False and safe:
                        self._set_unlock_blocked(False)
            elif phase_switch_cp_active:
                log.debug("Keine Actor-Bewegung, da CP-Unterbrechung oder Phasenumschaltung aktiv.")
            else:
                if self.chargepoint_state.plug_state is True and actor == ActorState.OPENED:
                    self.__close_actor()
                if self.chargepoint_state.plug_state is False and actor == ActorState.CLOSED:
                    self.__open_actor()
            return self.chargepoint_state

    def __open_actor(self):
        self.__set_actor(open=True)

    def __close_actor(self):
        self.__set_actor(open=False)

    # max 10 Versuche innerhalb der letzten 60 Sekunden.
    @RateLimiter(max_calls=10, max_seconds=60)
    def __set_actor(self, open: bool):
        GPIO.output(23, GPIO.LOW if open else GPIO.HIGH)
        GPIO.output(26, GPIO.HIGH)
        try:
            time.sleep(1)
        finally:
            GPIO.output(26, GPIO.LOW)
        log.debug("Actor opened" if open else "Actor closed")
