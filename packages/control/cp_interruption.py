""" Modul, das die CP-Unterbrechung durchführt.
"""
import threading
import time

from helpermodules.log import MainLogger
from helpermodules import pub
from modules.cp import ip_evse

cp_interruption_threads = {}


def thread_cp_interruption(cp_num, selected, config, duration):
    """ startet einen Thread pro Ladepunkt, an dem eine CP-Unterbrechung durchgeführt werden soll.
    Die CP-Unterbrechung erfolgt in Threads, da diese länger als ein Zyklus dauert.

    Parameter
    ---------
    cp_num: int
        Ladepunkt-Nummer
    selected: str
        Anbindungsmodul
    config: dict
        Konfiguration des Anbindungsmoduls
    duration: int
        Pausendauer
    """
    try:
        global cp_interruption_threads
        # fertige Threads aus der Liste löschen:
        cp_interruption_threads = {t: cp_interruption_threads[t]
                                   for t in cp_interruption_threads if cp_interruption_threads[t].is_alive()}

        # prüfen, ob Thread in der Liste ist. Dann ist noch eine Phasenumschaltung aktiv und es darf keine neue
        # gestartet werden.
        if "thread_cp"+str(cp_num) not in cp_interruption_threads:
            # Thread zur Phasenumschaltung erstellen, starten und der Liste hinzufügen.
            cp_interruption_threads["thread_cp"+str(cp_num)] = threading.Thread(
                target=_perform_cp_interruption, args=(selected, config, duration))
            cp_interruption_threads["thread_cp"+str(cp_num)].start()
            MainLogger().debug("Thread zur CP-Unterbrechung an LP"+str(cp_num)+" gestartet.")
    except Exception:
        MainLogger().exception("Fehler im Modul fuer die CP-Unterbrechung")


def _perform_cp_interruption(selected, config, duration):
    """ ruft das Modul zur Phasenumschaltung für das jeweilige Modul auf.
    """
    try:
        # Phasenumschaltung entsprechend Modul
        if selected == "external_openwb":
            ip_address = config["ip_address"]
            pub.pub_single("openWB/set/isss/Cpulp1", "1", ip_address)
            time.sleep(duration)
        elif selected == "ip_evse":
            ip_address = config["ip_address"]
            id = config["id"]
            ip_evse.perform_cp_interruption(ip_address, id, duration)
    except Exception:
        MainLogger().exception("Fehler im Modul fuer die CP-Unterbrechung")
