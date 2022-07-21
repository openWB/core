import logging
from typing import List
import copy
import threading
import time

from control import data
from control.chargepoint import AllChargepoints

log = logging.getLogger("soc."+__name__)


class UpdateSoc:
    def __init__(self) -> None:
        self.heartbeat = False

    def update(self) -> None:
        delay = 10
        next_time = time.time() + delay
        while True:
            self.heartbeat = True
            time.sleep(max(0, next_time - time.time()))
            try:
                threads = self.__get_threads()
                # Start them all
                if threads:
                    for thread in threads:
                        thread.start()

                    # Wait for all to complete
                    for thread in threads:
                        thread.join(timeout=10)

                    for thread in threads:
                        if thread.is_alive():
                            log.error("thread.name konnte nicht innerhalb des Timeouts die Werte abfragen, die "
                                      "abgefragten Werte werden nicht in der Regelung verwendet.")
            except Exception:
                log.exception("Fehler im Main-Modul")
            # skip tasks if we are behind schedule:
            next_time += (time.time() - next_time) // delay * delay + delay

    def __get_threads(self) -> List[threading.Thread]:
        threads = []
        cp_data = copy.deepcopy(data.data.cp_data)
        ev_data = copy.deepcopy(data.data.ev_data)
        # Alle Autos durchgehen
        for ev in ev_data.values():
            if ev.soc_module is not None:
                for cp in cp_data.values():
                    if not isinstance(cp, AllChargepoints):
                        if cp.data.set.charging_ev == ev.num:
                            charge_state = cp.data.get.charge_state
                            plug_state = cp.data.get.plug_state
                            break
                else:
                    charge_state = False
                    plug_state = False
                if ev.ev_template.soc_interval_expired(plug_state, charge_state, ev.data.get.soc_timestamp):
                    threads.append(threading.Thread(target=ev.soc_module.update,
                                                    args=(charge_state,), name=f"soc_ev{ev.num}"))
        return threads
