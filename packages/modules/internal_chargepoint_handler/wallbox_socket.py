import logging
import time
from typing import Optional

from helpermodules.utils.error_handling import ErrorTimerContext
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import ConsumerState
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_wallbox_socket_value_store
from modules.internal_chargepoint_handler.clients import ClientHandler
from modules.internal_chargepoint_handler.wallbox_socket_config import WallboxSocket

log = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
except ImportError:
    log.info("failed to import RPi.GPIO! maybe we are not running on a pi")


class WallboxSocketModule:
    def __init__(self, client_handler: ClientHandler, wallbox_socket: WallboxSocket) -> None:
        self.store_wallbox_socket = get_wallbox_socket_value_store()
        self.fault_state = FaultState(ComponentInfo(None, "Wallbox-Steckdose", "wallbox_socket"))
        self.client_error_context = ErrorTimerContext(
            "openWB/set/internal_socket/get/error_timestamp", "Wallbox-Steckdose bleibt ausgeschaltet.",
            hide_exception=True)
        self.client_error_context.error_timestamp = wallbox_socket.get.error_timestamp
        self._client = client_handler
        self.current_state = False
        self.old_wallbox_socket_state = ConsumerState(power=0, currents=[0]*3, powers=[0]*3, state=False)

    def get_values(self, last_tag: Optional[str] = None) -> ConsumerState:
        wallbox_socket_state = self.old_wallbox_socket_state
        with self.client_error_context:
            counter_state = self._client.request_and_check_wallbox_socket(self.fault_state)

            time.sleep(0.1)
            self.client_error_context.reset_error_counter()

            wallbox_socket_state = ConsumerState(
                power=counter_state.power,
                currents=counter_state.currents,
                imported=counter_state.imported,
                exported=counter_state.exported,
                powers=counter_state.powers,
                voltages=counter_state.voltages,
                state=self.current_state,
                rfid=last_tag,
            )

        if self.client_error_context.error_counter_exceeded():
            wallbox_socket_state = ConsumerState(
                power=0, currents=[0]*3, powers=[0]*3, state=False,
                imported=self.old_wallbox_socket_state.imported, exported=self.old_wallbox_socket_state.exported)

        self.store_wallbox_socket.set(wallbox_socket_state)
        self.store_wallbox_socket.update()
        self.old_wallbox_socket_state = wallbox_socket_state
        return self.old_wallbox_socket_state

    def set_state(self, state: bool) -> None:
        with SingleComponentUpdateContext(self.fault_state, update_always=False):
            direction_pin, enable_pin = self._client.get_pins_wallbox_socket()
            if state:
                GPIO.output(direction_pin, GPIO.HIGH)
                GPIO.output(enable_pin, GPIO.HIGH)
            else:
                GPIO.output(enable_pin, GPIO.LOW)
                GPIO.output(direction_pin, GPIO.LOW)
            self.current_state = state
