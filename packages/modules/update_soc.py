import logging
from typing import List, Tuple
import copy
import threading

from control import data
from control.chargepoint import AllChargepoints
from control.ev import Ev
from helpermodules import timecheck
from helpermodules.pub import Pub
from helpermodules.utils import thread_handler
from modules.common.abstract_soc import SocUpdateData

log = logging.getLogger("soc."+__name__)


class UpdateSoc:
    def __init__(self) -> None:
        self.heartbeat = False

    def update(self) -> None:
        try:
            threads_set, threads_update = self._get_threads()
            thread_handler(threads_set)
            thread_handler(threads_update)
        except Exception:
            log.exception("Fehler im Main-Modul")

    def _get_threads(self) -> Tuple[List[threading.Thread], List[threading.Thread]]:
        threads_set, threads_update = [], []
        ev_data = copy.deepcopy(data.data.ev_data)
        # Alle Autos durchgehen
        for ev in ev_data.values():
            try:
                if ev.soc_module is not None:
                    soc_update_data = self._get_soc_update_data(ev.num)
                    if (ev.ev_template.soc_interval_expired(soc_update_data.charge_state, ev.data.get.soc_timestamp) or
                            ev.data.get.force_soc_update):
                        self._reset_force_soc_update(ev)
                        # Es wird ein Zeitstempel gesetzt, unabhängig ob die Abfrage erfolgreich war, da einige
                        # Hersteller bei zu häufigen Abfragen Accounts sperren.
                        Pub().pub(f"openWB/set/vehicle/{ev.num}/get/soc_timestamp", timecheck.create_timestamp())
                        threads_set.append(threading.Thread(target=ev.soc_module.update,
                                                            args=(soc_update_data,), name=f"soc_ev{ev.num}"))
                        if hasattr(ev.soc_module, "store"):
                            threads_update.append(threading.Thread(target=ev.soc_module.store.update,
                                                                   args=(), name=f"soc_ev{ev.num}"))
            except Exception:
                log.exception("Fehler im Main-Modul")
        return threads_set, threads_update

    def _reset_force_soc_update(self, ev: Ev) -> None:
        if ev.data.get.force_soc_update:
            ev.data.get.force_soc_update = False
            Pub().pub(f"openWB/set/vehicle/{ev.num}/get/force_soc_update", False)

    def _get_soc_update_data(self, ev_num: int) -> SocUpdateData:
        cp_data = copy.deepcopy(data.data.cp_data)
        for cp in cp_data.values():
            if not isinstance(cp, AllChargepoints):
                if cp.data.config.ev == ev_num:
                    charge_state = cp.data.get.charge_state
                    break
        else:
            charge_state = False
        return SocUpdateData(charge_state=charge_state)
