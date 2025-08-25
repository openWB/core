""" Modul, das die Phasenumschaltung durchführt.
"""
import logging
from threading import Thread

from helpermodules.utils._thread_handler import is_thread_alive, thread_handler
from modules.common.abstract_chargepoint import AbstractChargepoint

log = logging.getLogger(__name__)


def thread_phase_switch(cp) -> None:
    """ startet einen Thread pro Ladepunkt, an dem eine Phasenumschaltung durchgeführt werden soll. Die
    Phasenumschaltung erfolgt in Threads, da diese länger als ein Zyklus dauert.
    """
    try:
        log.debug("Starte Thread zur Phasenumschaltung an LP"+str(cp.num))
        return thread_handler(Thread(
            target=_perform_phase_switch,
            args=(cp.chargepoint_module,
                  cp.data.control_parameter.phases),
            name=f"phase switch cp{cp.chargepoint_module.config.id}"))
    except Exception:
        log.exception("Fehler im Phasenumschaltungs-Modul")


def _perform_phase_switch(chargepoint_module: AbstractChargepoint, phases: int) -> None:
    """ ruft das Modul zur Phasenumschaltung für das jeweilige Modul auf.
    """
    # Stoppen der Ladung wird in start_charging bei gesetztem phase_switch_timestamp durchgeführt.
    # Wenn gerade geladen wird, muss vor der Umschaltung eine Pause von 5s gemacht werden.
    try:
        # Phasenumschaltung entsprechend Modul
        chargepoint_module.switch_phases(phases)
    except Exception:
        log.exception("Fehler im Phasenumschaltungs-Modul")


def phase_switch_thread_alive(cp_num):
    return is_thread_alive(f"phase switch cp{cp_num}")
