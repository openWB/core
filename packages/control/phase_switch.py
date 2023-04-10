""" Modul, das die Phasenumschaltung durchführt.
"""
import logging
import threading
import time
from typing import Dict

from control.ev import Ev
from modules.common.abstract_chargepoint import AbstractChargepoint

log = logging.getLogger(__name__)
phase_switch_threads: Dict[str, threading.Thread] = {}


def thread_phase_switch(cp) -> None:
    """ startet einen Thread pro Ladepunkt, an dem eine Phasenumschaltung durchgeführt werden soll. Die
    Phasenumschaltung erfolgt in Threads, da diese länger als ein Zyklus dauert.
    """
    try:
        global phase_switch_threads
        # fertige Threads aus der Liste löschen:
        phase_switch_threads = {
            t: phase_switch_threads[t] for t in phase_switch_threads if phase_switch_threads[t].is_alive()}

        # prüfen, ob Thread in der Liste ist. Dann ist noch eine Phasenumschaltung aktiv und es darf keine neue
        # gestartet werden.
        if "thread_cp"+str(cp.num) not in phase_switch_threads:
            # Thread zur Phasenumschaltung erstellen, starten und der Liste hinzufügen.
            phase_switch_threads["thread_cp"+str(cp.num)] = threading.Thread(
                target=_perform_phase_switch,
                args=(cp.chargepoint_module,
                      cp.data.set.charging_ev_data,
                      cp.data.get.charge_state),
                name=f"cp{cp.chargepoint_module.id}")
            phase_switch_threads["thread_cp"+str(cp.num)].start()
            log.debug("Thread zur Phasenumschaltung an LP"+str(cp.num)+" gestartet.")
    except Exception:
        log.exception("Fehler im Phasenumschaltungs-Modul")


def _perform_phase_switch(chargepoint_module: AbstractChargepoint, ev: Ev, charge_state: bool) -> None:
    """ ruft das Modul zur Phasenumschaltung für das jeweilige Modul auf.
    """
    # Stoppen der Ladung wird in start_charging bei gesetztem phase_switch_timestamp durchgeführt.
    # Wenn gerade geladen wird, muss vor der Umschaltung eine Pause von 5s gemacht werden.
    try:
        if charge_state:
            time.sleep(5)
        # Phasenumschaltung entsprechend Modul
        chargepoint_module.switch_phases(ev.data.control_parameter.phases, ev.ev_template.data.phase_switch_pause)
        # Die Ladung wird in start_charging wieder gestartet, wenn phase_switch_timestamp wieder auf None gesetzt wird.
        time.sleep(ev.ev_template.data.keep_charge_active_duration)
    except Exception:
        log.exception("Fehler im Phasenumschaltungs-Modul")


def phase_switch_thread_alive(cp_num):
    if f"thread_cp{cp_num}" in phase_switch_threads:
        return phase_switch_threads[f"thread_cp{cp_num}"].is_alive()
    else:
        return False
