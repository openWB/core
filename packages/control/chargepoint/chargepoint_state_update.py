import copy
import logging
from threading import Thread
import threading
from typing import Dict

from control.chargepoint.chargepoint import Chargepoint
from helpermodules.utils import thread_handler


log = logging.getLogger(__name__)


class ChargepointStateUpdate:
    def __init__(self,
                 index: int,
                 event_copy_data: threading.Event,
                 event_global_data_initialized: threading.Event,
                 cp_template_data: Dict,
                 ev_data: Dict,
                 ev_charge_template_data: Dict,
                 ev_template_data: Dict) -> None:
        self.event_update_state = threading.Event()
        self.event_copy_data = event_copy_data
        self.event_global_data_initialized = event_global_data_initialized
        self.chargepoint: Chargepoint = Chargepoint(index, self.event_update_state)
        self.cp_template_data = cp_template_data
        self.ev_data = ev_data
        self.ev_charge_template_data = ev_charge_template_data
        self.ev_template_data = ev_template_data
        thread_handler(Thread(target=self.update, args=(), name=f"ChargepointStateUpdate cp {index}"))

    def update(self):
        self.event_global_data_initialized.wait()
        while self.event_update_state.wait():
            try:
                self.event_copy_data.clear()
                # Workaround, da mit Python3.9/pymodbus2.5 eine pymodbus-Instanz nicht mehr kopiert werden kann.
                # Bei einer Neukonfiguration eines Device/Komponente wird dieses neu initialisiert. Nur bei Komponenten
                # mit simcount werden Werte aktualisiert, diese sollten jedoch nur einmal nach dem Auslesen aktualisiert
                # werden, sodass die Nutzung einer Referenz vorerst funktioniert.
                # Verwendung der Referenz führt bei der Pro zu Instabilität.
                try:
                    cp = copy.deepcopy(self.chargepoint)
                except TypeError:
                    cp = Chargepoint(self.chargepoint.num, None)
                    cp.data = copy.deepcopy(self.chargepoint.data)
                    cp.chargepoint_module = self.chargepoint.chargepoint_module
                cp.template = copy.deepcopy(self.cp_template_data[f"cpt{self.chargepoint.data.config.template}"])
                ev_list = {}
                for ev in self.ev_data:
                    ev_list[ev] = copy.deepcopy(self.ev_data[ev])
                for vehicle in ev_list:
                    try:
                        ev_list[vehicle].charge_template = copy.deepcopy(self.ev_charge_template_data["ct" + str(
                            ev_list[vehicle].data.charge_template)])
                        # zuerst das aktuelle Profil laden
                        ev_list[vehicle].ev_template = copy.deepcopy(self.ev_template_data["et" + str(
                            ev_list[vehicle].data.ev_template)])
                    except Exception:
                        log.exception("Fehler im Prepare-Modul für EV "+str(vehicle))
                self.event_copy_data.set()
                cp.update_ev(ev_list)
                self.event_update_state.clear()
            except Exception:
                log.exception("Fehler ChargepointStateUpdate")
                self.event_copy_data.set()
                self.event_update_state.clear()
