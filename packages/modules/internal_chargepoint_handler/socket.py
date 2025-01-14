from enum import IntEnum
import functools
import logging
import time
from typing import Callable

from helpermodules.hardware_configuration import get_hardware_configuration_setting
from helpermodules.logger import ModifyLoglevelContext
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import ChargepointState
from modules.internal_chargepoint_handler.chargepoint_module import ChargepointModule
from modules.internal_chargepoint_handler.clients import ClientHandler


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
                 parent_hostname: str,
                 parent_cp: int,
                 hierarchy_id: int) -> None:
        self.socket_max_current = get_hardware_configuration_setting("max_c_socket")
        with ModifyLoglevelContext(log, logging.DEBUG):
            log.info(f"Konfiguration als Buchse mit maximal {self.socket_max_current}A Ladestrom je Phase.")
        super().__init__(local_charge_point_num, client_handler, parent_hostname, parent_cp, hierarchy_id)

    def set_current(self, current: float) -> None:
        with SingleComponentUpdateContext(self.fault_state, update_always=False):
            with self.client_error_context:
                actor = ActorState(GPIO.input(19))

                if actor == ActorState.CLOSED:
                    if current == self.set_current_evse:
                        return
                else:
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
            if phase_switch_cp_active:
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
        time.sleep(1)
        GPIO.output(26, GPIO.LOW)
        log.debug("Actor opened" if open else "Actor closed")
