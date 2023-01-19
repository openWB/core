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

log = logging.getLogger(__name__)


class UpdateSoc:
    def __init__(self) -> None:
        self.heartbeat = False
        self.event_vehicle_update_completed = Event()
        self.event_vehicle_update_completed.set()

    def update(self) -> None:
        topic = "openWB/set/vehicle/set/vehicle_update_completed"
        try:
            threads_update, threads_store = self._get_threads()
            with ModuleUpdateCompletedContext(self.event_vehicle_update_completed, topic):
                threads_update, threads_store = self._get_threads()
                thread_handler(threads_update)
            with ModuleUpdateCompletedContext(self.event_vehicle_update_completed, topic):
                threads_store = self._filter_failed_store_threads(threads_store)
                thread_handler(threads_store)
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
                    if (ev.soc_interval_expired(soc_update_data.charge_state) or ev.data.get.force_soc_update):
                        self._reset_force_soc_update(ev)
                        if ev.data.get.fault_state == 2:
                            ev.data.set.soc_error_counter += 1
                        else:
                            ev.data.set.soc_error_counter = 0
                        Pub().pub(f"openWB/set/vehicle/{ev.num}/set/soc_error_counter", ev.data.set.soc_error_counter)
                        if ev.data.set.soc_error_counter > 3:
                            log.debug(
                                f"EV{ev.num}: Nach dreimaliger erfolgloser SoC-Abfrage wird ein SoC von 0% angenommen.")
                            Pub().pub(f"openWB/set/vehicle/{ev.num}/get/soc", 0)
                            Pub().pub(f"openWB/set/vehicle/{ev.num}/get/range", 0)
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

    def _filter_failed_store_threads(self, threads_store: List[Thread]) -> List[Thread]:
        ev_data = copy.deepcopy(subdata.SubData.ev_data)
        # Alle Autos durchgehen, deren SoC gerade aktualisiert wurde
        for ev_thread in threads_store:
            try:
                ev = ev_data[f"ev{ev_thread.getName()[6:]}"]
                if ev.soc_module is not None:
                    if hasattr(ev.soc_module, "store"):
                        if ev.data.get.fault_state == 2:
                            threads_store.remove(ev_thread)
            except Exception:
                log.exception("Fehler im update_soc-Modul")
        return threads_store
