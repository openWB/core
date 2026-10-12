"""Optional Series2 socket: one bus reader, shared measurements and actor output."""
import copy
import logging
import threading
import time
from typing import Optional

from modules.common.component_state import ConsumerState, CounterState
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.fault_state_level import FaultStateLevel
from modules.common.modbus import ModbusDataType
from modules.common.sdm import Sdm120

log = logging.getLogger(__name__)


class LocalSocket:
    MODBUS_ID = 54
    DIRECTION_PIN = 23  # BOARD numbering, BCM 11
    ENABLE_PIN = 26  # BOARD numbering, BCM 7
    POLL_INTERVAL = 5
    RETRY_INTERVAL = 60
    MAX_AGE = 15

    def __init__(self):
        self._lock = threading.RLock()
        self._gpio = None
        self._meter = None
        self._client = None
        self._meter_fault = None
        self._fault_state = FaultState(ComponentInfo(None, "Lokale Steckdosenmessung", "consumer"))
        self._values: Optional[CounterState] = None
        self._timestamp = 0.0
        self._next_poll = 0.0
        self._present = False
        self._state = False
        self._fault_state.error("Steckdosenmessung noch nicht initialisiert.")

    def start(self, client, fault_state):
        import RPi.GPIO as GPIO

        with self._lock:
            self._gpio = GPIO
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(self.ENABLE_PIN, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(self.DIRECTION_PIN, GPIO.OUT, initial=GPIO.LOW)
            self._client = client
            self._meter_fault = fault_state
            self._meter = None
            self._values = None
            self._timestamp = 0.0
            self._next_poll = 0.0
            self._present = False
            self._state = False
            self._fault_state.error("SDM120 an Adresse 54 noch nicht erkannt.")

    def poll(self):
        """Called exclusively by the internal chargepoint's bus polling thread."""
        now = time.monotonic()
        if self._client is None or now < self._next_poll:
            return
        try:
            self._meter_fault.no_error()
            if not self._present:
                voltage = self._client.read_input_registers(
                    0, ModbusDataType.FLOAT_32, unit=self.MODBUS_ID)
                if not 100 < voltage < 300:
                    raise ValueError(f"Unplausible SDM120-Spannung: {voltage}")
            if self._meter is None:
                self._meter = Sdm120(self.MODBUS_ID, self._client, self._meter_fault)
            values = self._meter.get_counter_state()
            with self._lock:
                self._values = values
                self._timestamp = time.monotonic()
                self._present = True
                self._fault_state.from_exception(self._meter_fault)
            self._next_poll = time.monotonic() + self.POLL_INTERVAL
        except Exception as error:
            with self._lock:
                self._fault_state.error(f"SDM120 an Adresse 54 nicht erreichbar: {error}")
                self._present = False
                self._set_output(False)
            self._next_poll = time.monotonic() + self.RETRY_INTERVAL
            log.warning("Steckdosenmessung: %s", error)

    def _set_output(self, state: bool):
        if self._gpio is not None:
            if state:
                self._gpio.output(self.DIRECTION_PIN, self._gpio.HIGH)
                self._gpio.output(self.ENABLE_PIN, self._gpio.HIGH)
            else:
                self._gpio.output(self.ENABLE_PIN, self._gpio.LOW)
                self._gpio.output(self.DIRECTION_PIN, self._gpio.LOW)
        self._state = state

    def switch(self, state: bool):
        with self._lock:
            if state:
                self._check_values()
            self._set_output(state)

    def get_fault(self):
        """Transfer the measurement fault to the consumer's regular fault context."""
        with self._lock:
            if self._present and time.monotonic() - self._timestamp > self.MAX_AGE:
                self._set_output(False)
                self._present = False
                self._fault_state.error("Steckdosenmesswerte sind veraltet.")
            return self._fault_state.fault_state, self._fault_state.fault_str

    def _check_values(self):
        level, message = self.get_fault()
        if level == FaultStateLevel.ERROR or self._values is None or not self._present:
            fault = FaultState(self._fault_state.component_info)
            fault.error(message)
            raise fault

    def get_state(self) -> ConsumerState:
        with self._lock:
            self._check_values()
            values = copy.deepcopy(self._values)
            return ConsumerState(power=values.power, imported=values.imported, exported=values.exported,
                                 voltages=values.voltages, currents=values.currents, powers=values.powers,
                                 state=self._state)

    def stop(self):
        with self._lock:
            self._set_output(False)
            self._meter = None
            self._client = None
            self._meter_fault = None
            self._present = False
            self._fault_state.error("Interner Ladepunkthandler für die Steckdose nicht aktiv.")


local_socket = LocalSocket()
