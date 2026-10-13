import logging
import time

from helpermodules.utils.error_handling import ErrorTimerContext
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import ConsumerState, InternalSocketState
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_internal_socket_value_store
from modules.internal_chargepoint_handler.clients import ClientHandler
from modules.internal_chargepoint_handler.internal_socket_config import InternalSocket

log = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
except ImportError:
    log.info("failed to import RPi.GPIO! maybe we are not running on a pi")


class SocketModule:
    def __init__(self, client_handler: ClientHandler, internal_socket: InternalSocket) -> None:
        self.store_internal = get_internal_socket_value_store()
        self.fault_state = FaultState(ComponentInfo(None, "Interne Steckdose", "internal_socket"))
        self.client_error_context = ErrorTimerContext(
            "openWB/set/internal_socket/get/error_timestamp", "Steckdose bleibt ausgeschaltet.",
            hide_exception=True)
        self.client_error_context.error_timestamp = internal_socket.get.error_timestamp
        self._client = client_handler
        self.current_state = False

    def get_values(self) -> InternalSocketState:
        with self.client_error_context:
            counter_state = self._client.request_and_check_socket(self.fault_state)

            time.sleep(0.1)
            self.client_error_context.reset_error_counter()

            chargepoint_state = ConsumerState(
                power=counter_state.power,
                currents=counter_state.currents,
                imported=counter_state.imported,
                exported=counter_state.exported,
                powers=counter_state.powers,
                voltages=counter_state.voltages,
                state=self.current_state,
            )

        return chargepoint_state

    def set_state(self, state: bool) -> None:
        with SingleComponentUpdateContext(self.fault_state, update_always=False):
            direction_pin, enable_pin = self._client.get_pins_socket()
            if state:
                GPIO.output(direction_pin, GPIO.HIGH)
                GPIO.output(enable_pin, GPIO.HIGH)
            else:
                GPIO.output(enable_pin, GPIO.LOW)
                GPIO.output(direction_pin, GPIO.LOW)
            self.current_state = state
