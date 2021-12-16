""" Modul, das die Phasenumschaltung durchführt.
"""
import threading
import time

from helpermodules.log import MainLogger
from modules.common.abstract_chargepoint import AbstractChargepoint


phase_switch_threads = {}


def thread_phase_switch(
        cp_num: int, chargepoint_module: AbstractChargepoint, phases_to_use: int, duration: int, charge_state: bool) -> None:
    """ startet einen Thread pro Ladepunkt, an dem eine Phasenumschaltung durchgeführt werden soll. Die
    Phasenumschaltung erfolgt in Threads, da diese länger als ein Zyklus dauert.

    Parameter
    ---------
    cp_num: int
        Ladepunkt-Nummer
    selected: str
        Anbindungsmodul
    config: dict
        Konfiguration des Anbindungsmoduls
    phases_to_use: int
        Anzahl Phasen, die nach der Umschaltung verwendet werden sollen
    duration: int
        Pause vor und nach der Umschaltung
    charge_state: int
        Ladung aktiv/inaktiv
    """
    try:
        global phase_switch_threads
        # fertige Threads aus der Liste löschen:
        phase_switch_threads = {
            t: phase_switch_threads[t] for t in phase_switch_threads if phase_switch_threads[t].is_alive()}

        # prüfen, ob Thread in der Liste ist. Dann ist noch eine Phasenumschaltung aktiv und es darf keine neue
        # gestartet werden.
        if "thread_cp"+str(cp_num) not in phase_switch_threads:
            # Thread zur Phasenumschaltung erstellen, starten und der Liste hinzufügen.
            phase_switch_threads["thread_cp"+str(cp_num)] = threading.Thread(
                target=_perform_phase_switch, args=(chargepoint_module, phases_to_use, duration, charge_state))
            phase_switch_threads["thread_cp"+str(cp_num)].start()
            MainLogger().debug("Thread zur Phasenumschaltung an LP"+str(cp_num)+" gestartet.")
    except Exception:
        MainLogger().exception("Fehler im Phasenumschaltungs-Modul")


def _perform_phase_switch(
        chargepoint_module: AbstractChargepoint, phases_to_use: int, duration: int, charge_state: bool) -> None:
    """ ruft das Modul zur Phasenumschaltung für das jeweilige Modul auf.
    """
    # Stoppen der Ladung wird in start_charging bei gesetztem phase_switch_timestamp durchgeführt.
    # Wenn gerade geladen wird, muss vor der Umschaltung eine Pause von 5s gemacht werden.
    try:
        if charge_state:
            time.sleep(5)
        # Phasenumschaltung entsprechend Modul
        chargepoint_module.switch_phases(phases_to_use, duration)
        # Kurze Pause, bevor mit der Ladung gestartet wird.
        # Die Ladung wird in start_charging wieder gestartet, wenn phase_switch_timestamp wieder auf "0" gesetzt wird.
        if charge_state:
            time.sleep(1)
    except Exception:
        MainLogger().exception("Fehler im Phasenumschaltungs-Modul")
