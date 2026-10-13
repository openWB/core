import logging
import time

from helpermodules.utils.error_handling import ErrorTimerContext
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import InternalSocketState
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.fault_state_level import FaultStateLevel
from modules.common.store import get_internal_socket_value_store
from modules.internal_chargepoint_handler.clients import SocketClientHandler
from modules.internal_chargepoint_handler.internal_socket_config import InternalSocket, MAX_MEASUREMENT_AGE

log = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
except ImportError:
    log.info("failed to import RPi.GPIO! maybe we are not running on a pi")


class SocketModule:
    POLL_INTERVAL = 5
    RETRY_INTERVAL = 60

    def __init__(self, client_handler: SocketClientHandler, internal_socket: InternalSocket) -> None:
        self.fault_state = FaultState(ComponentInfo(None, "Interne Steckdose", "internal_socket"))
        self.fault_state.error("Steckdosenmessung noch nicht initialisiert.")
        self.store_internal = get_internal_socket_value_store()
        self.client_error_context = ErrorTimerContext(
            "openWB/set/internal_socket/get/error_timestamp", "Steckdose bleibt ausgeschaltet.",
            hide_exception=True)
        self.client_error_context.error_timestamp = internal_socket.get.error_timestamp
        self.old_socket_state = InternalSocketState(state=False)
        self._client = client_handler
        self._next_poll = 0.0
        self._measurement_time = 0.0
        direction_pin, enable_pin = self._client.get_pins_socket()
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(enable_pin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(direction_pin, GPIO.OUT, initial=GPIO.LOW)

    def get_values(self) -> InternalSocketState:
        if time.monotonic() >= self._next_poll:
            self._next_poll = time.monotonic() + self.RETRY_INTERVAL
            try:
                with self.client_error_context:
                    try:
                        self.fault_state.no_error()
                        counter_state = self._client.request_and_check_hardware(self.fault_state)
                    except Exception:
                        self._set_output(False)
                        self._store_state()
                        raise
                    self.old_socket_state = InternalSocketState(
                        power=counter_state.power,
                        currents=counter_state.currents,
                        imported=counter_state.imported,
                        exported=counter_state.exported,
                        powers=counter_state.powers,
                        voltages=counter_state.voltages,
                        state=self.old_socket_state.state,
                        timestamp=time.time())
                    self._measurement_time = time.monotonic()
                    self._next_poll = self._measurement_time + self.POLL_INTERVAL
                    self.client_error_context.reset_error_counter()
            except Exception:
                self._set_output(False)
                self._store_state()
                raise
        if self.client_error_context.error_counter_exceeded():
            self._set_output(False)
        elif self.client_error_context.error_timestamp is None:
            self._check_measurement_age()
        self._store_state()
        return self.old_socket_state

    def set_state(self, state: bool) -> None:
        with SingleComponentUpdateContext(self.fault_state, update_always=False):
            if state:
                self._check_measurement_age()
                if (self.client_error_context.error_timestamp is not None or
                        self.fault_state.fault_state == FaultStateLevel.ERROR or
                        self.old_socket_state.timestamp == 0):
                    raise self.fault_state
            self._set_output(state)
            self._store_state()

    def _check_measurement_age(self) -> None:
        if self.fault_state.fault_state == FaultStateLevel.ERROR:
            self._set_output(False)
        elif time.monotonic() - self._measurement_time > MAX_MEASUREMENT_AGE:
            self._set_output(False)
            self.fault_state.error("Steckdosenmesswerte sind veraltet.")

    def _set_output(self, state: bool) -> None:
        direction_pin, enable_pin = self._client.get_pins_socket()
        if state:
            GPIO.output(direction_pin, GPIO.HIGH)
            GPIO.output(enable_pin, GPIO.HIGH)
        else:
            GPIO.output(enable_pin, GPIO.LOW)
            GPIO.output(direction_pin, GPIO.LOW)
        self.old_socket_state.state = state

    def _store_state(self) -> None:
        self.store_internal.set(self.old_socket_state)
        self.store_internal.update()
