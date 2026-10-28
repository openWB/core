import logging
import time
from typing import Optional, Tuple, Union

from helpermodules.utils.error_handling import ErrorTimerContext
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import ConsumerState, CounterState
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.hardware_check import check_meter
from modules.common.modbus import ModbusSerialClient_, ModbusTcpClient_
from modules.common.store import get_wallbox_socket_value_store
from modules.internal_chargepoint_handler.hardware_definition import CP0_METERS, WALLBOX_SOCKET_METERS, MeterClient
from modules.internal_chargepoint_handler.internal_hardware_check import (
    METER_NO_SERIAL_NUMBER, METER_PROBLEM, READ_LAN_ADAPTER_AGAIN, READ_USB_ADAPTER_AGAIN)
from modules.internal_chargepoint_handler.wallbox_socket_config import WallboxSocket

log = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
except ImportError:
    log.info("failed to import RPi.GPIO! maybe we are not running on a pi")


class WallboxSocketModule:
    def __init__(self, client: Union[ModbusSerialClient_, ModbusTcpClient_], wallbox_socket: WallboxSocket) -> None:
        self.store_wallbox_socket = get_wallbox_socket_value_store()
        self.fault_state = FaultState(ComponentInfo(None, "Wallbox-Steckdose", "wallbox_socket"))
        self.client_error_context = ErrorTimerContext(
            "openWB/set/internal_socket/get/error_timestamp", "Wallbox-Steckdose bleibt ausgeschaltet.",
            hide_exception=True)
        self.client_error_context.error_timestamp = wallbox_socket.get.error_timestamp
        self._client = client
        meter_type, modbus_id = WALLBOX_SOCKET_METERS[0]
        self.meter_client = meter_type(modbus_id, client, self.fault_state)
        self.current_state = False
        self.old_wallbox_socket_state = ConsumerState(power=0, currents=[0]*3, powers=[0]*3, state=False)

    def check_meter(self, meter_client: MeterClient) -> Tuple[bool, Optional[str], Optional[CounterState]]:
        try:
            with self._client:
                counter_state = meter_client.get_counter_state()
            if counter_state.serial_number == "0" or counter_state.serial_number is None:
                log.warning(METER_NO_SERIAL_NUMBER)
            return True, check_meter(counter_state), counter_state
        except Exception:
            return False, METER_PROBLEM, None

    def request_and_check_wallbox_socket(self) -> CounterState:
        meter_check_passed, meter_error_msg, counter_state = self.check_meter(self.meter_client)
        if meter_check_passed is False:
            # Probe the chargepoint meter only to distinguish a meter failure from a bus failure.
            for meter_type, modbus_id in CP0_METERS:
                diagnostic_meter = meter_type(modbus_id, self._client, self.fault_state)
                if self.check_meter(diagnostic_meter)[0]:
                    raise Exception(meter_error_msg)
            raise Exception(READ_USB_ADAPTER_AGAIN)
        if meter_error_msg is not None:
            self.fault_state.warning(meter_error_msg)
        return counter_state

    def get_values(self, last_tag: Optional[str] = None) -> ConsumerState:
        wallbox_socket_state = self.old_wallbox_socket_state
        with self.client_error_context:
            counter_state = self.request_and_check_wallbox_socket()

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
            direction_pin, enable_pin = 23, 26  # BOARD numbering: BCM 11, BCM 7
            if state:
                GPIO.output(direction_pin, GPIO.HIGH)
                GPIO.output(enable_pin, GPIO.HIGH)
            else:
                GPIO.output(enable_pin, GPIO.LOW)
                GPIO.output(direction_pin, GPIO.LOW)
            self.current_state = state
