import logging

import time
from helpermodules.logger import ModifyLoglevelContext

from helpermodules.utils.error_handling import CP_ERROR, ErrorTimerContext
from modules.common.abstract_chargepoint import AbstractChargepoint
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import ChargepointState
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_internal_chargepoint_value_store, get_chargepoint_value_store
from modules.internal_chargepoint_handler.clients import ClientHandler

log = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
except ImportError:
    log.info("failed to import RPi.GPIO! maybe we are not running on a pi")


class ChargepointModule(AbstractChargepoint):
    PLUG_STANDBY_POWER_THRESHOLD = 10

    def __init__(self, local_charge_point_num: int,
                 client_handler: ClientHandler,
                 parent_hostname: str,
                 parent_cp: int,
                 hierarchy_id: int) -> None:
        self.local_charge_point_num = local_charge_point_num
        self.fault_state = FaultState(ComponentInfo(
            hierarchy_id,
            "Ladepunkt "+str(local_charge_point_num),
            "chargepoint",
            parent_id=parent_cp,
            parent_hostname=parent_hostname))
        self.store_internal = get_internal_chargepoint_value_store(local_charge_point_num)
        self.store = get_chargepoint_value_store(hierarchy_id)
        self.client_error_context = ErrorTimerContext(
            f"openWB/set/internal_chargepoint/{local_charge_point_num}/get/error_timestamp",
            CP_ERROR,
            hide_exception=True)
        self.old_plug_state = False
        self.old_phases_in_use = 0
        self.old_chargepoint_state = ChargepointState()
        self._client = client_handler
        version = self._client.evse_client.get_firmware_version()
        with ModifyLoglevelContext(log, logging.DEBUG):
            log.debug(f"Firmware-Version der EVSE: {version}")
        if version < 17:
            self._precise_current = False
        else:
            if self._client.evse_client.is_precise_current_active() is False:
                self._client.evse_client.activate_precise_current()
            self._precise_current = self._client.evse_client.is_precise_current_active()
        self.max_evse_current = self._client.evse_client.get_max_current()

    def set_current(self, current: float) -> None:
        with SingleComponentUpdateContext(self.fault_state, update_always=False):
            formatted_current = int(current*100) if self._precise_current else int(current)
            if self.set_current_evse != formatted_current:
                self._client.evse_client.set_current(formatted_current)

    def get_values(self, phase_switch_cp_active: bool, last_tag: str) -> ChargepointState:
        def store_state(chargepoint_state: ChargepointState) -> None:
            self.store.set(chargepoint_state)
            self.store.update()
            self.store_internal.set(chargepoint_state)
            self.store_internal.update()
        with self.client_error_context:
            chargepoint_state = self.old_chargepoint_state
            self.set_current_evse = chargepoint_state.evse_current

            self._client.check_hardware(self.fault_state)
            powers, power = self._client.meter_client.get_power()
            if power < self.PLUG_STANDBY_POWER_THRESHOLD:
                power = 0
            voltages = self._client.meter_client.get_voltages()
            currents = self._client.meter_client.get_currents()
            imported = self._client.meter_client.get_imported()
            power_factors = self._client.meter_client.get_power_factors()
            frequency = self._client.meter_client.get_frequency()
            serial_number = self._client.meter_client.get_serial_number()
            phases_in_use = sum(1 for current in currents if current > 3)
            if phases_in_use == 0:
                phases_in_use = self.old_phases_in_use
            else:
                self.old_phases_in_use = phases_in_use

            time.sleep(0.1)
            plug_state, charge_state, self.set_current_evse = self._client.evse_client.get_plug_charge_state()
            self.client_error_context.reset_error_counter()

            if phase_switch_cp_active:
                # Während des Threads wird die CP-Leitung unterbrochen, das EV soll aber als angesteckt betrachtet
                # werden. In 1.9 war das kein Problem, da währenddessen keine Werte von der EVSE abgefragt wurden.
                log.debug(
                    "Plug_state %s beibehalten, da CP-Unterbrechung oder Phasenumschaltung aktiv.", self.old_plug_state
                )
                plug_state = self.old_plug_state
            else:
                self.old_plug_state = plug_state

            chargepoint_state = ChargepointState(
                power=power,
                currents=currents,
                imported=imported,
                exported=0,
                powers=powers,
                voltages=voltages,
                frequency=frequency,
                plug_state=plug_state,
                charge_state=charge_state,
                phases_in_use=phases_in_use,
                power_factors=power_factors,
                rfid=last_tag,
                evse_current=self.set_current_evse,
                serial_number=serial_number,
                max_evse_current=self.max_evse_current
            )
        if self.client_error_context.error_counter_exceeded():
            chargepoint_state = ChargepointState()
            chargepoint_state.plug_state = False
            chargepoint_state.charge_state = False
            chargepoint_state.imported = self.old_chargepoint_state.imported
            chargepoint_state.exported = self.old_chargepoint_state.exported

        store_state(chargepoint_state)
        self.old_chargepoint_state = chargepoint_state
        return chargepoint_state

    def perform_phase_switch(self, phases_to_use: int, duration: int) -> None:
        gpio_cp, gpio_relay = self._client.get_pins_phase_switch(phases_to_use)
        with SingleComponentUpdateContext(self.fault_state, update_always=False):
            self._client.evse_client.set_current(0)
        time.sleep(1)
        GPIO.output(gpio_cp, GPIO.HIGH)  # CP off
        GPIO.output(gpio_relay, GPIO.HIGH)  # 3 on/off
        time.sleep(duration)
        GPIO.output(gpio_relay, GPIO.LOW)  # 3 on/off
        time.sleep(duration)
        GPIO.output(gpio_cp, GPIO.LOW)  # CP on
        time.sleep(1)

    def perform_cp_interruption(self, duration: int) -> None:
        gpio_cp = self._client.get_pins_cp_interruption()
        with SingleComponentUpdateContext(self.fault_state, update_always=False):
            self._client.evse_client.set_current(0)
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(gpio_cp, GPIO.OUT)

        GPIO.output(gpio_cp, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(gpio_cp, GPIO.LOW)
