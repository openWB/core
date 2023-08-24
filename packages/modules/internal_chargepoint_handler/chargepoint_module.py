import logging

import time
from typing import Tuple

from modules.common.abstract_chargepoint import AbstractChargepoint
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import ChargepointState
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_internal_chargepoint_value_store
from modules.internal_chargepoint_handler.clients import ClientHandler

log = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
except ImportError:
    log.info("failed to import RPi.GPIO! maybe we are not running on a pi")


class ChargepointModule(AbstractChargepoint):
    PLUG_STANDBY_POWER_THRESHOLD = 10

    def __init__(self, local_charge_point_num: int, client_handler: ClientHandler, parent_hostname: str) -> None:
        self.local_charge_point_num = local_charge_point_num
        self.component_info = ComponentInfo(
            local_charge_point_num,
            "Ladepunkt "+str(local_charge_point_num), "internal_chargepoint", parent_hostname)
        self.store = get_internal_chargepoint_value_store(local_charge_point_num)
        self.old_plug_state = False
        self.old_phases_in_use = 0
        self.__client = client_handler
        version = self.__client.evse_client.get_firmware_version()
        if version < 17:
            self._precise_current = False
        else:
            if self.__client.evse_client.is_precise_current_active() is False:
                self.__client.evse_client.activate_precise_current()
            self._precise_current = self.__client.evse_client.is_precise_current_active()

    def set_current(self, current: float) -> None:
        with SingleComponentUpdateContext(self.component_info):
            formatted_current = int(current*100) if self._precise_current else int(current)
            if self.set_current_evse != formatted_current:
                self.__client.evse_client.set_current(formatted_current)

    def get_values(self, phase_switch_cp_active: bool, last_tag: str) -> Tuple[ChargepointState, float]:
        try:
            powers, power = self.__client.meter_client.get_power()
            if power < self.PLUG_STANDBY_POWER_THRESHOLD:
                power = 0
            voltages = self.__client.meter_client.get_voltages()
            currents = self.__client.meter_client.get_currents()
            imported = self.__client.meter_client.get_imported()
            power_factors = self.__client.meter_client.get_power_factors()
            frequency = self.__client.meter_client.get_frequency()
            phases_in_use = sum(1 for current in currents if current > 3)
            if phases_in_use == 0:
                phases_in_use = self.old_phases_in_use
            else:
                self.old_phases_in_use = phases_in_use

            time.sleep(0.1)
            plug_state, charge_state, self.set_current_evse = self.__client.evse_client.get_plug_charge_state()
            self.__client.read_error = 0

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
                rfid=last_tag
            )
        except Exception as e:
            self.__client.read_error += 1
            if self.__client.read_error > 5:
                log.exception(
                    "Anhaltender Fehler beim Auslesen der EVSE. Lade- und Stecker-Status werden zurückgesetzt.")
                plug_state = False
                charge_state = False
                chargepoint_state = ChargepointState(
                    plug_state=plug_state,
                    charge_state=charge_state,
                    phases_in_use=0
                )
                FaultState.error(__name__ + " " + str(type(e)) + " " + str(e)).store_error(self.component_info)
            else:
                self.__client.check_hardware()
                raise FaultState.error(__name__ + " " + str(type(e)) + " " + str(e)) from e

        self.store.set(chargepoint_state)
        self.store.update()
        return chargepoint_state, self.set_current_evse

    def perform_phase_switch(self, phases_to_use: int, duration: int) -> None:
        gpio_cp, gpio_relay = self.__client.get_pins_phase_switch(phases_to_use)
        with SingleComponentUpdateContext(self.component_info):
            self.__client.evse_client.set_current(0)
        time.sleep(1)
        GPIO.output(gpio_cp, GPIO.HIGH)  # CP off
        GPIO.output(gpio_relay, GPIO.HIGH)  # 3 on/off
        time.sleep(duration)
        GPIO.output(gpio_relay, GPIO.LOW)  # 3 on/off
        time.sleep(duration)
        GPIO.output(gpio_cp, GPIO.LOW)  # CP on
        time.sleep(1)

    def perform_cp_interruption(self, duration: int) -> None:
        gpio_cp = self.__client.get_pins_cp_interruption()
        with SingleComponentUpdateContext(self.component_info):
            self.__client.evse_client.set_current(0)
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(gpio_cp, GPIO.OUT)

        GPIO.output(gpio_cp, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(gpio_cp, GPIO.LOW)
