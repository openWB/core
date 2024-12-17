import logging
import threading
from typing import List, Tuple
import copy
from threading import Event, Thread

from control import data
from control.ev.ev import Ev
from helpermodules import subdata
from helpermodules import timecheck
from helpermodules.constants import NO_ERROR
from helpermodules.pub import Pub
from helpermodules.utils import joined_thread_handler
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.utils import wait_for_module_update_completed

log = logging.getLogger(__name__)


class UpdateSoc:
    def __init__(self, event_update_soc: threading.Event) -> None:
        self.heartbeat = False
        self.event_vehicle_update_completed = Event()
        self.event_vehicle_update_completed.set()
        self.event_update_soc = event_update_soc

    def update(self) -> None:
        # kein ChangedValuesHandler, da dieser mit data.data arbeitet
        while True:
            self.event_update_soc.wait(timeout=10)
            self.event_update_soc.clear()
            topic = "openWB/set/vehicle/set/vehicle_update_completed"
            try:
                threads_update, threads_store = self._get_threads()
                joined_thread_handler(threads_update, 300)
                wait_for_module_update_completed(self.event_vehicle_update_completed, topic)
                # threads_store = self._filter_failed_store_threads(threads_store)
                joined_thread_handler(threads_store, data.data.general_data.data.control_interval/3)
                wait_for_module_update_completed(self.event_vehicle_update_completed, topic)
            except Exception:
                log.exception("Fehler im update_soc-Modul")

    def _get_threads(self) -> Tuple[List[Thread], List[Thread]]:
        threads_update, threads_store = [], []
        ev_data = copy.deepcopy(subdata.SubData.ev_data)
        # Alle Autos durchgehen
        for ev in ev_data.values():
            try:
                if ev.soc_module is not None:
                    vehicle_update_data = self._get_vehicle_update_data(ev.num)
                    if (ev.soc_interval_expired(vehicle_update_data) or ev.data.get.force_soc_update):
                        self._reset_force_soc_update(ev)
                        if ev.data.get.fault_state == 2:
                            ev.data.set.soc_error_counter += 1
                        else:
                            ev.data.set.soc_error_counter = 0
                        Pub().pub(f"openWB/set/vehicle/{ev.num}/set/soc_error_counter", ev.data.set.soc_error_counter)
                        if ev.data.set.soc_error_counter >= 3:
                            log.debug(
                                f"EV{ev.num}: Nach dreimaliger erfolgloser SoC-Abfrage wird ein SoC von 0% angenommen.")
                            Pub().pub(f"openWB/set/vehicle/{ev.num}/get/soc", 0)
                            Pub().pub(f"openWB/set/vehicle/{ev.num}/get/range", 0)
                        # Es wird ein Zeitstempel gesetzt, unabhängig ob die Abfrage erfolgreich war, da einige
                        # Hersteller bei zu häufigen Abfragen Accounts sperren.
                        Pub().pub(f"openWB/set/vehicle/{ev.num}/get/soc_request_timestamp",
                                  timecheck.create_timestamp())
                        threads_update.append(Thread(target=ev.soc_module.update,
                                                     args=(vehicle_update_data,), name=f"fetch soc_ev{ev.num}"))
                        if hasattr(ev.soc_module, "store"):
                            threads_store.append(Thread(target=ev.soc_module.store.update,
                                                        args=(), name=f"store soc_ev{ev.num}"))
                else:
                    # Wenn kein Modul konfiguriert ist, Fehlerstatus zurücksetzen.
                    if ev.data.get.fault_state != 0:
                        Pub().pub(f"openWB/set/vehicle/{ev.num}/get/fault_state", 0)
                    if ev.data.get.fault_str != NO_ERROR:
                        Pub().pub(f"openWB/set/vehicle/{ev.num}/get/fault_str", NO_ERROR)
                    if ev.data.get.soc is not None:
                        Pub().pub(f"openWB/set/vehicle/{ev.num}/get/soc", None)
                    if ev.data.get.soc_timestamp is not None:
                        Pub().pub(f"openWB/set/vehicle/{ev.num}/get/soc_timestamp", None)
                    if ev.data.get.soc_request_timestamp is not None:
                        Pub().pub(f"openWB/set/vehicle/{ev.num}/get/soc_request_timestamp", None)
                    if ev.data.get.range is not None:
                        Pub().pub(f"openWB/set/vehicle/{ev.num}/get/range", None)
            except Exception:
                log.exception("Fehler im update_soc-Modul")
        return threads_update, threads_store

    def _reset_force_soc_update(self, ev: Ev) -> None:
        if ev.data.get.force_soc_update:
            ev.data.get.force_soc_update = False
            Pub().pub(f"openWB/set/vehicle/{ev.num}/get/force_soc_update", False)

    def _get_vehicle_update_data(self, ev_num: int) -> VehicleUpdateData:
        ev = subdata.SubData.ev_data[f"ev{ev_num}"]
        ev_template = subdata.SubData.ev_template_data[f"et{ev.data.ev_template}"]
        for cp_state_update in list(subdata.SubData.cp_data.values()):
            cp = cp_state_update.chargepoint
            if cp.data.set.charging_ev == ev_num or cp.data.set.charging_ev_prev == ev_num:
                plug_state = cp.data.get.plug_state
                charge_state = cp.data.get.charge_state
                imported = cp.data.get.imported
                if ev.soc_module.general_config.use_soc_from_cp:
                    soc_from_cp = cp.data.get.soc
                    timestamp_soc_from_cp = cp.data.get.soc_timestamp
                else:
                    soc_from_cp = None
                    timestamp_soc_from_cp = None
                break
        else:
            plug_state = False
            charge_state = False
            imported = None
            soc_from_cp = None
            timestamp_soc_from_cp = None
        battery_capacity = ev_template.data.battery_capacity
        efficiency = ev_template.data.efficiency
        soc_timestamp = ev.data.get.soc_timestamp
        return VehicleUpdateData(plug_state=plug_state,
                                 charge_state=charge_state,
                                 efficiency=efficiency,
                                 imported=imported,
                                 battery_capacity=battery_capacity,
                                 soc_from_cp=soc_from_cp,
                                 timestamp_soc_from_cp=timestamp_soc_from_cp,
                                 soc_timestamp=soc_timestamp)

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
