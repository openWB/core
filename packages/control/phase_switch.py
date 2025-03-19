""" Modul, das die Phasenumschaltung durchführt.
"""
import logging
import threading
import time

from control.ev.ev import Ev
from helpermodules.utils._thread_handler import is_thread_alive, thread_handler
from modules.common.abstract_chargepoint import AbstractChargepoint

log = logging.getLogger(__name__)


def thread_phase_switch(cp) -> None:
    """ startet einen Thread pro Ladepunkt, an dem eine Phasenumschaltung durchgeführt werden soll. Die
    Phasenumschaltung erfolgt in Threads, da diese länger als ein Zyklus dauert.
    """
    try:
        if thread_handler(threading.Thread(
                target=_perform_phase_switch,
                args=(cp.chargepoint_module,
                      cp.data.control_parameter.phases,
                      cp.data.set.charging_ev_data,
                      cp.data.get.charge_state),
                name=f"phase switch cp{cp.chargepoint_module.config.id}")):
            log.debug("Thread zur Phasenumschaltung an LP"+str(cp.num)+" gestartet.")
    except Exception:
        log.exception("Fehler im Phasenumschaltungs-Modul")


def _perform_phase_switch(chargepoint_module: AbstractChargepoint, phases: int, ev: Ev, charge_state: bool) -> None:
    """ ruft das Modul zur Phasenumschaltung für das jeweilige Modul auf.
    """
    # Stoppen der Ladung wird in start_charging bei gesetztem phase_switch_timestamp durchgeführt.
    # Wenn gerade geladen wird, muss vor der Umschaltung eine Pause von 5s gemacht werden.
    try:
        if charge_state:
            time.sleep(5)
        # Phasenumschaltung entsprechend Modul
        chargepoint_module.switch_phases(phases, ev.ev_template.data.phase_switch_pause)
        # Die Ladung wird in start_charging wieder gestartet, wenn phase_switch_timestamp wieder auf None gesetzt wird.
        time.sleep(ev.ev_template.data.keep_charge_active_duration)
    except Exception:
        log.exception("Fehler im Phasenumschaltungs-Modul")


def phase_switch_thread_alive(cp_num):
    return is_thread_alive(f"phase switch cp{cp_num}")
