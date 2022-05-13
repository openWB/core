""" Modul, das die CP-Unterbrechung durchführt.
"""
import logging
import threading

from modules.common.abstract_chargepoint import AbstractChargepoint

log = logging.getLogger(__name__)

cp_interruption_threads = {}


def thread_cp_interruption(cp_num: int, chargepoint_module: AbstractChargepoint, duration: int):
    """ startet einen Thread pro Ladepunkt, an dem eine CP-Unterbrechung durchgeführt werden soll.
    Die CP-Unterbrechung erfolgt in Threads, da diese länger als ein Zyklus dauert.
    """
    try:
        global cp_interruption_threads
        # fertige Threads aus der Liste löschen:
        cp_interruption_threads = {t: cp_interruption_threads[t]
                                   for t in cp_interruption_threads if cp_interruption_threads[t].is_alive()}

        # prüfen, ob Thread in der Liste ist. Dann ist noch eine CP-Unterbrechung aktiv und es darf keine neue
        # gestartet werden.
        if "thread_cp"+str(cp_num) not in cp_interruption_threads:
            cp_interruption_threads["thread_cp"+str(cp_num)] = threading.Thread(
                target=chargepoint_module.interrupt_cp, args=(duration,))
            cp_interruption_threads["thread_cp"+str(cp_num)].start()
            log.debug("Thread zur CP-Unterbrechung an LP"+str(cp_num)+" gestartet.")
        else:
            log.debug(f"Kein Thread zur CP-Unterbrechung an LP{cp_num} gestartet, da bereits eine CP-Unterbrechung "
                      f"aktiv ist.")
    except Exception:
        log.exception("Fehler im Modul für die CP-Unterbrechung")
