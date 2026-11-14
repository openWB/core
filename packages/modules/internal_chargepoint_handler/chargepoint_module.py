import logging
from typing import List, Optional

import time
from helpermodules.broker import BrokerClient

from helpermodules.utils import run_command
from helpermodules.utils.error_handling import CP_ERROR, ErrorTimerContext
from helpermodules.utils.topic_parser import decode_payload
from modules.common.abstract_chargepoint import AbstractChargepoint
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import ChargepointState
from modules.common.evse import EvseStatusCode
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_internal_chargepoint_value_store, get_chargepoint_value_store
from modules.internal_chargepoint_handler.clients import ClientHandler
from helpermodules.subdata import SubData
from modules.internal_chargepoint_handler.internal_chargepoint_handler_config import InternalChargepoint

log = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
except ImportError:
    log.info("failed to import RPi.GPIO! maybe we are not running on a pi")


class ChargepointModule(AbstractChargepoint):
    PLUG_STANDBY_POWER_THRESHOLD = 10

    def __init__(self, local_charge_point_num: int,
                 client_handler: ClientHandler,
                 internal_cp: InternalChargepoint,
                 hierarchy_id: int) -> None:
        self.local_charge_point_num = local_charge_point_num
        self.fault_state = FaultState(ComponentInfo(
            local_charge_point_num,
            "Ladepunkt "+str(local_charge_point_num),
            "internal_chargepoint",
            hierarchy_id=hierarchy_id))
        self.store_internal = get_internal_chargepoint_value_store(local_charge_point_num)
        self.store = get_chargepoint_value_store(hierarchy_id)
        self.client_error_context = ErrorTimerContext(
            f"openWB/set/internal_chargepoint/{local_charge_point_num}/get/error_timestamp",
            CP_ERROR,
            hide_exception=True)
        self.client_error_context.error_timestamp = internal_cp.get.error_timestamp
        self.old_plug_state = False
        self.old_chargepoint_state = ChargepointState(plug_state=False,
                                                      charge_state=False,
                                                      imported=None,
                                                      exported=None,
                                                      currents=None,
                                                      phases_in_use=0,
                                                      power=0)
        self._client = client_handler

        self.version = SubData.system_data["system"].data["version"]
        self.current_branch = SubData.system_data["system"].data["current_branch"]
        self.current_commit = SubData.system_data["system"].data["current_commit"]

        if float(run_command.run_command(["cat", "/proc/uptime"]).split(" ")[0]) < 180:
            self.perform_phase_switch(1)
            self.old_phases_in_use = 1
        else:
            def on_connect(client, userdata, flags, rc):
                client.subscribe(f"openWB/internal_chargepoint/{self.local_charge_point_num}/get/phases_in_use")

            def on_message(client, userdata, message):
                self.old_phases_in_use = decode_payload(message.payload)

            self.old_phases_in_use = 1
            BrokerClient(f"subscribeInternalCp{self.local_charge_point_num}",
                         on_connect, on_message).start_finite_loop()

    def set_current(self, current: float) -> None:
        with SingleComponentUpdateContext(self.fault_state, update_always=False):
            self._client.evse_client.set_current(current, phases_in_use=self.old_phases_in_use)

    def get_values(self, phase_switch_cp_active: bool, last_tag: str) -> ChargepointState:
        def store_state(chargepoint_state: ChargepointState) -> None:
            self.store.set(chargepoint_state)
            self.store.update()
            self.store_internal.set(chargepoint_state)
            self.store_internal.update()
        with self.client_error_context:
            chargepoint_state = self.old_chargepoint_state

            evse_state, counter_state = self._client.request_and_check_hardware(self.fault_state)
            power = counter_state.power
            if counter_state.power < self.PLUG_STANDBY_POWER_THRESHOLD:
                power = 0
            phases_in_use = sum(1 for current in counter_state.currents if current > 3)
            if phases_in_use == 0:
                phases_in_use = self.old_phases_in_use
            else:
                self.old_phases_in_use = phases_in_use

            time.sleep(0.1)
            self.client_error_context.reset_error_counter()

            if phase_switch_cp_active:
                # Während des Threads wird die CP-Leitung unterbrochen, das EV soll aber als angesteckt betrachtet
                # werden. In 1.9 war das kein Problem, da währenddessen keine Werte von der EVSE abgefragt wurden.
                log.debug(
                    "Plug_state %s beibehalten, da CP-Unterbrechung oder Phasenumschaltung aktiv.", self.old_plug_state
                )
                plug_state = self.old_plug_state
            else:
                self.old_plug_state = evse_state.plug_state
                plug_state = evse_state.plug_state

            chargepoint_state = ChargepointState(
                power=power,
                currents=counter_state.currents,
                imported=counter_state.imported,
                exported=0,
                powers=counter_state.powers,
                voltages=counter_state.voltages,
                frequency=counter_state.frequency,
                plug_state=plug_state,
                charge_state=evse_state.charge_state,
                phases_in_use=phases_in_use,
                power_factors=counter_state.power_factors,
                rfid=last_tag,
                evse_current=evse_state.set_current,
                serial_number=counter_state.serial_number,
                max_evse_current=evse_state.max_current,
                version=self.version,
                current_branch=self.current_branch,
                current_commit=self.current_commit
            )
        if self.client_error_context.error_counter_exceeded():
            chargepoint_state = ChargepointState(plug_state=self.old_plug_state,
                                                 charge_state=False,
                                                 imported=self.old_chargepoint_state.imported,
                                                 exported=self.old_chargepoint_state.exported,
                                                 currents=[0]*3,
                                                 phases_in_use=self.old_chargepoint_state.phases_in_use,
                                                 power=0)

        store_state(chargepoint_state)
        self.old_chargepoint_state = chargepoint_state
        return chargepoint_state

    # Issue #4289: Vor dem CP-Trennen muss der Zähler 0 A zeigen UND die EVSE das Fahrzeug in State A/B melden
    # (Statusregister 1002 = 1/2). Der EVSE-Sollwert (Register 1000) taugt nicht als Kriterium, er steht
    # sofort nach set_current(0) auf 0 (#3326). Ein einzelner Busfehler beim Rücklesen bricht nicht ab;
    # erst ohne Bestätigung im Zeitfenster wird abgebrochen (Exception -> FaultState, keine GPIO-Aktion).
    PHASE_SWITCH_CURRENT_THRESHOLD_A = 0.5   # MPM3PM zeigt bei offenem EV-Schütz 0,0 A, SDM/B23 rauschen
    PHASE_SWITCH_METER_POLLS = 20            # 20 x (0,5 s + Lesezeit) = 10-20 s

    @classmethod
    def _vehicle_stopped_charging(cls, currents: Optional[List[Optional[float]]], evse_state: int) -> bool:
        # Status 3/4 = State C/D (lädt), 5 = Fehler: beides keine Bestätigung
        if evse_state not in (EvseStatusCode.READY, EvseStatusCode.EV_PRESENT):
            return False
        if currents is None:  # kein Zähler vorhanden, nur der EVSE-Status zählt
            return True
        # jede Phase braucht einen gültigen Messwert unter der Schwelle; None (z. B. NaN vom B23) zählt nicht als 0 A,
        # Vorzeichen (Zähler verkehrt herum eingebaut) spielt keine Rolle
        return len(currents) == 3 and all(
            c is not None and abs(c) < cls.PHASE_SWITCH_CURRENT_THRESHOLD_A for c in currents)

    def perform_phase_switch(self, phases_to_use: int) -> None:
        gpio_cp, gpio_relay = self._client.get_pins_phase_switch(phases_to_use)
        evse = self._client.evse_client
        meter = self._client.meter_client
        num = self.local_charge_point_num
        start = time.monotonic()
        with SingleComponentUpdateContext(self.fault_state, update_always=False, reraise=True):
            if meter is None:
                log.warning(f"Phasenumschaltung LP{num}: kein Zähler gefunden, es wird nur der EVSE-Status geprüft.")
            evse.set_current(0)  # Schreibfehler -> Abbruch: ohne 0-A-Vorgabe wird nicht geschaltet (#3326)
            for poll in range(1, self.PHASE_SWITCH_METER_POLLS + 1):
                try:
                    # Status aus dieser Lesung verwenden, nicht aus einem geteilten Attribut: der reguläre
                    # Zyklus liest die EVSE parallel und könnte sonst einen älteren Wert hinterlassen
                    state = evse.get_state_number()
                    currents = meter.get_counter_state().currents if meter is not None else None
                    log.debug(f"Phasenumschaltung LP{num}: Durchlauf {poll}, Ströme {currents} A, EVSE-Status {state}")
                    if self._vehicle_stopped_charging(currents, state):
                        log.warning(f"Phasenumschaltung LP{num}: 0 A und EVSE-Status {state} nach {poll} Durchläufen"
                                    f" / {time.monotonic() - start:.1f} s bestätigt, Ströme {currents} A.")
                        break
                except Exception as e:
                    # einzelner Busfehler (EVSE und Zähler am selben RS485-Bus): weiter pollen
                    log.warning(f"Phasenumschaltung LP{num}: Rücklesen fehlgeschlagen ({e}), weiter.")
                time.sleep(0.5)
                try:
                    evse.set_current(0)
                except Exception as e:
                    log.warning(f"Phasenumschaltung LP{num}: 0 A setzen fehlgeschlagen ({e}), weiter.")
            else:
                raise Exception("Fahrzeug hat die Ladung nicht beendet (Zählerstrom > 0 oder EVSE-Status C)"
                                " - Phasenumschaltung abgebrochen.")
        try:
            GPIO.output(gpio_cp, GPIO.HIGH)  # CP off
            GPIO.output(gpio_relay, GPIO.HIGH)  # 3 on/off
            time.sleep(5)
            GPIO.output(gpio_relay, GPIO.LOW)  # 3 on/off
            time.sleep(5)
        finally:
            GPIO.output(gpio_cp, GPIO.LOW)  # CP on - in jedem Fall wieder verbinden (#4037)
        time.sleep(1)
        self.old_phases_in_use = phases_to_use
        log.warning(f"Phasenumschaltung LP{num}: auf {phases_to_use} Phasen umgeschaltet "
                    f"({time.monotonic() - start:.1f} s gesamt).")

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
