import logging
from typing import List, Tuple
import copy
from threading import Event, Thread

from control import data
from control.chargepoint import AllChargepoints
from control.ev import Ev
from helpermodules import subdata
from helpermodules import timecheck
from helpermodules.pub import Pub
from helpermodules.utils import thread_handler
from modules.common.abstract_soc import SocUpdateData
from modules.utils import ModuleUpdateCompletedContext

log = logging.getLogger("soc."+__name__)


class UpdateSoc:
    def __init__(self) -> None:
        self.heartbeat = False
        self.event_module_update_completed = Event()

    def update(self) -> None:
        try:
            threads_update, threads_store = self._get_threads()
            with ModuleUpdateCompletedContext(self.event_module_update_completed):
                threads_update, threads_store = self._get_threads()
                thread_handler(threads_update)
            with ModuleUpdateCompletedContext(self.event_module_update_completed):
                threads_store, threads_failed = self._filter_failed_store_threads(threads_store)
                thread_handler(threads_store)
                self._reset_failed_soc_request(threads_failed)
        except Exception:
            log.exception("Fehler im update_soc-Modul")

    def _get_threads(self) -> Tuple[List[Thread], List[Thread]]:
        threads_update, threads_store = [], []
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
                        threads_update.append(Thread(target=ev.soc_module.update,
                                                     args=(soc_update_data,), name=f"soc_ev{ev.num}"))
                        if hasattr(ev.soc_module, "store"):
                            threads_store.append(Thread(target=ev.soc_module.store.update,
                                                        args=(), name=f"soc_ev{ev.num}"))
            except Exception:
                log.exception("Fehler im update_soc-Modul")
        return threads_update, threads_store

    def _reset_force_soc_update(self, ev: Ev) -> None:
        if ev.data.get.force_soc_update:
            ev.data.get.force_soc_update = False
            Pub().pub(f"openWB/set/vehicle/{ev.num}/get/force_soc_update", False)

    def _get_soc_update_data(self, ev_num: int) -> SocUpdateData:
        for cp in list(data.data.cp_data.values()):
            if not isinstance(cp, AllChargepoints):
                if cp.data.set.charging_ev == ev_num:
                    charge_state = cp.data.get.charge_state
                    break
        else:
            charge_state = False
        return SocUpdateData(charge_state=charge_state)

    def _filter_failed_store_threads(self, threads_store: List[Thread]) -> Tuple[List[Thread], List[Thread]]:
        ev_data = copy.deepcopy(subdata.SubData.ev_data)
        threads_failed = []
        # Alle Autos durchgehen, deren SoC gerade aktualisiert wurde
        for ev_thread in threads_store:
            try:
                ev = ev_data[f"ev{ev_thread.getName()[6:]}"]
                if ev.soc_module is not None:
                    if hasattr(ev.soc_module, "store"):
                        if ev.data.get.fault_state == 2:
                            threads_failed.append(ev_thread)
                            threads_store.remove(ev_thread)
            except Exception:
                log.exception("Fehler im update_soc-Modul")
        return threads_store, threads_failed

    def _reset_failed_soc_request(self, threads_failed: List[Thread]) -> None:
        ev_data = copy.deepcopy(subdata.SubData.ev_data)
        # Alle Autos durchgehen, deren SoC gerade aktualisiert wurde
        for ev_thread in threads_failed:
            try:
                ev = ev_data[f"ev{ev_thread.getName()[6:]}"]
                log.debug(f"Zurücksetzen des SoC für EV{ev.num}, da ein Fehler vorliegt.")
                Pub().pub(f"openWB/set/vehicle/{ev.num}/get/soc", 0)
                Pub().pub(f"openWB/set/vehicle/{ev.num}/get/range", 0)
            except Exception:
                log.exception("Fehler im update_soc-Modul")
