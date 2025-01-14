""" Verschachtelte Listen, die die Daten zur Berechnung des Algorithmus enthalten.
Dictionary: Zugriff erfolgt bei Dictionary über Keys, nicht über Indizes wie bei Listen. Das hat den Vorteil, dass
Instanzen gelöscht werden können, der Zugriff aber nicht verändert werden muss.
"""
import copy
import logging
import threading
from functools import wraps
from typing import Dict
from control.bat import Bat
from control.bat_all import BatAll
from control.chargepoint.chargepoint import Chargepoint
from control.chargepoint.chargepoint_all import AllChargepoints
from control.chargepoint.chargepoint_template import CpTemplate
from control.pv import Pv
from control.pv_all import PvAll

import dataclass_utils
from helpermodules.graph import Graph
from helpermodules.subdata import SubData
from control.counter import Counter
from control.counter_all import CounterAll
from control.ev.charge_template import ChargeTemplate
from control.ev.ev import Ev
from control.ev.ev_template import EvTemplate
from control.general import General
from control.optional import Optional
from modules.common.abstract_device import AbstractDevice

log = logging.getLogger(__name__)
bat_data_lock = threading.Lock()
bat_all_data_lock = threading.Lock()
graph_data_lock = threading.Lock()
counter_data_lock = threading.Lock()
counter_all_data_lock = threading.Lock()
cp_data_lock = threading.Lock()
cp_all_data_lock = threading.Lock()
cp_template_data_lock = threading.Lock()
ev_charge_template_data_lock = threading.Lock()
ev_data_lock = threading.Lock()
ev_template_data_lock = threading.Lock()
general_data_lock = threading.Lock()
optional_data_lock = threading.Lock()
pv_data_lock = threading.Lock()
pv_all_data_lock = threading.Lock()
system_data_lock = threading.Lock()


def locked(lock: threading.Lock):
    def decorate(method):
        @wraps(method)
        def inner(*args, **kwargs):
            # context handler may be used if no logging of lock duration required: "with lock:..."
            try:
                lock.acquire()
                return method(*args, **kwargs)
            finally:
                lock.release()
        return inner
    return decorate


class Data:
    def __init__(self, event_module_update_completed: threading.Event):
        self.event_module_update_completed = event_module_update_completed
        self._bat_data: Dict[str, Bat] = {}
        self._bat_all_data = BatAll()
        self._counter_data: Dict[str, Counter] = {}
        self._counter_all_data = CounterAll()
        self._cp_data: Dict[str, Chargepoint] = {}
        self._cp_all_data = AllChargepoints()
        self._cp_template_data: Dict[str, CpTemplate] = {}
        self._ev_charge_template_data: Dict[str, ChargeTemplate] = {}
        self._ev_data: Dict[str, Ev] = {}
        self._ev_template_data: Dict[str, EvTemplate] = {}
        self._general_data = General()
        self._graph_data = Graph()
        self._optional_data = Optional()
        self._pv_data: Dict[str, Pv] = {}
        self._pv_all_data = PvAll()
        self._system_data = {}

    # getter-Funktion, der Zugriff erfolgt wie bei einem Zugriff auf eine öffentliche Variable.
    @property
    def bat_data(self) -> Dict[str, Bat]:
        """ gibt die Variable zurück. """
        return self._bat_data

    @bat_data.setter
    @locked(bat_data_lock)
    def bat_data(self, value):
        """ setzt die Variable. Durch das Lock wird verhindert, dass gleichzeitig geschrieben wird.

        Parameter
        ---------
        value: Wert, der gesetzt werden soll.
        """
        self._bat_data = value

    @property
    def bat_all_data(self) -> BatAll:
        return self._bat_all_data

    @bat_all_data.setter
    @locked(bat_all_data_lock)
    def bat_all_data(self, value):
        self._bat_all_data = value

    @property
    def graph_data(self) -> Graph:
        return self._graph_data

    @graph_data.setter
    @locked(graph_data_lock)
    def graph_data(self, value):
        self._graph_data = value

    @property
    def counter_data(self) -> Dict[str, Counter]:
        return self._counter_data

    @counter_data.setter
    @locked(counter_data_lock)
    def counter_data(self, value):
        self._counter_data = value

    @property
    def counter_all_data(self) -> CounterAll:
        return self._counter_all_data

    @counter_all_data.setter
    @locked(counter_all_data_lock)
    def counter_all_data(self, value):
        self._counter_all_data = value

    @property
    def cp_data(self) -> Dict[str, Chargepoint]:
        return self._cp_data

    @cp_data.setter
    @locked(cp_data_lock)
    def cp_data(self, value):
        self._cp_data = value

    @property
    def cp_all_data(self) -> AllChargepoints:
        return self._cp_all_data

    @cp_all_data.setter
    @locked(cp_all_data_lock)
    def cp_all_data(self, value):
        self._cp_all_data = value

    @property
    def cp_template_data(self):
        return self._cp_template_data

    @cp_template_data.setter
    @locked(cp_template_data_lock)
    def cp_template_data(self, value):
        self._cp_template_data = value

    @property
    def ev_charge_template_data(self) -> Dict[str, ChargeTemplate]:
        return self._ev_charge_template_data

    @ev_charge_template_data.setter
    @locked(ev_charge_template_data_lock)
    def ev_charge_template_data(self, value):
        self._ev_charge_template_data = value

    @property
    @locked(ev_data_lock)
    def ev_data(self) -> Dict[str, Ev]:
        return self._ev_data

    @ev_data.setter
    @locked(ev_data_lock)
    def ev_data(self, value):
        self._ev_data = value

    @property
    def ev_template_data(self) -> Dict[str, EvTemplate]:
        return self._ev_template_data

    @ev_template_data .setter
    @locked(ev_template_data_lock)
    def ev_template_data(self, value):
        self._ev_template_data = value

    @property
    def general_data(self) -> General:
        return self._general_data

    @general_data.setter
    @locked(general_data_lock)
    def general_data(self, value):
        self._general_data = value

    @property
    def optional_data(self) -> Optional:
        return self._optional_data

    @optional_data.setter
    @locked(optional_data_lock)
    def optional_data(self, value):
        self._optional_data = value

    @property
    def pv_data(self) -> Dict[str, Pv]:
        return self._pv_data

    @pv_data.setter
    @locked(pv_data_lock)
    def pv_data(self, value):
        self._pv_data = value

    @property
    def pv_all_data(self) -> PvAll:
        return self._pv_all_data

    @pv_all_data.setter
    @locked(pv_all_data_lock)
    def pv_all_data(self, value):
        self._pv_all_data = value

    @property
    def system_data(self):
        return self._system_data

    @system_data.setter
    @locked(system_data_lock)
    def system_data(self, value):
        self._system_data = value

    def print_all(self):
        self._print_dictionaries(self._bat_data)
        log.info(f"bat_all_data\n{self._bat_all_data.data}")
        log.info(f"cp_all_data\n{self._cp_all_data.data}")
        self._print_dictionaries(self._cp_data)
        self._print_dictionaries(self._cp_template_data)
        self._print_dictionaries(self._counter_data)
        log.info(f"counter_all_data\n{self._counter_all_data.data}")
        self._print_dictionaries(self._ev_charge_template_data)
        self._print_dictionaries(self._ev_data)
        self._print_dictionaries(self._ev_template_data)
        log.info(f"general_data\n{self._general_data.data}")
        log.info(f"general_data-display\n{self._general_data.data.extern_display_mode}")
        log.info(f"graph_data\n{self._graph_data.data}")
        log.info(f"optional_data\n{self._optional_data.data}")
        self._print_dictionaries(self._pv_data)
        log.info(f"pv_all_data\n{self._pv_all_data.data}")
        self._print_dictionaries(self._system_data)
        self._print_device_config(self._system_data)
        log.info("\n")

    def _print_dictionaries(self, data):
        """ gibt zu Debug-Zwecken für jeden Key im übergebenen Dictionary das Dictionary aus.

        Parameter
        ---------
        data: dict
        """
        for key in data:
            try:
                if not isinstance(data[key], dict):
                    try:
                        log.info(key+"\n"+str(data[key].data))
                    except AttributeError:
                        # Devices haben kein data-Dict
                        pass
                else:
                    log.info(key+"\n"+"Klasse fehlt")
            except Exception:
                log.exception("Fehler im Data-Modul")

    def _print_device_config(self, data: Dict[str, AbstractDevice]):
        for key, value in data.items():
            try:
                if isinstance(value, AbstractDevice):
                    log.info(f"{key}\n{dataclass_utils.asdict(value.device_config)}")
                    for comp_key, comp_value in value.components.items():
                        log.info(f"{comp_key}\n{dataclass_utils.asdict(comp_value.component_config)}")
            except Exception:
                log.exception("Fehler im Data-Modul")

    def copy_system_data(self) -> None:
        with ModuleDataReceivedContext(self.event_module_update_completed):
            self.__copy_system_data()

    def __copy_system_data(self) -> None:
        """ kopiert die Daten, die per MQTT empfangen wurden.
        """
        try:
            # Workaround, da mit Python3.9/pymodbus2.5 eine pymodbus-Instanz nicht mehr kopiert werden kann.
            # Bei einer Neukonfiguration eines Device/Komponente wird dieses neu initialisiert. Nur bei Komponenten
            # mit simcount werden Werte aktualisiert, diese sollten jedoch nur einmal nach dem Auslesen aktualisiert
            # werden, sodass die Nutzung einer Referenz vorerst funktioniert.
            self.system_data = {
                "system": copy.deepcopy(SubData.system_data["system"])} | {
                k: SubData.system_data[k] for k in SubData.system_data if "device" in k}
            self.general_data = copy.deepcopy(SubData.general_data)
            self.__copy_cp_data()
        except Exception:
            log.exception("Fehler im Prepare-Modul")

    def __copy_counter_data(self) -> None:
        self.counter_all_data = copy.deepcopy(SubData.counter_all_data)
        self.counter_data.clear()
        for counter in SubData.counter_data:
            stop = False
            if counter != "all":
                for dev in SubData.system_data:
                    if "device" in dev:
                        for component in SubData.system_data[dev].components:
                            if component[9:] == counter[7:]:
                                self.counter_data[counter] = copy.deepcopy(SubData.counter_data[counter])
                                stop = True
                                break
                    if stop:
                        break
            else:
                self.counter_data[counter] = copy.deepcopy(SubData.counter_data[counter])

    def __copy_cp_data(self) -> None:
        self.cp_data.clear()
        for cp in SubData.cp_data:
            # Workaround, da mit Python3.9/pymodbus2.5 eine pymodbus-Instanz nicht mehr kopiert werden kann.
            # Bei einer Neukonfiguration eines Device/Komponente wird dieses neu initialisiert. Nur bei Komponenten
            # mit simcount werden Werte aktualisiert, diese sollten jedoch nur einmal nach dem Auslesen aktualisiert
            # werden, sodass die Nutzung einer Referenz vorerst funktioniert.
            # Verwendung der Referenz führt bei der Pro zu Instabilität.
            try:
                self.cp_data[cp] = copy.deepcopy(SubData.cp_data[cp].chargepoint)
            except TypeError:
                self.cp_data[cp] = Chargepoint(SubData.cp_data[cp].chargepoint.num, None)
                self.cp_data[cp].template = copy.deepcopy(SubData.cp_data[cp].chargepoint.template)
                self.cp_data[cp].data = copy.deepcopy(SubData.cp_data[cp].chargepoint.data)
                self.cp_data[cp].chargepoint_module = SubData.cp_data[cp].chargepoint.chargepoint_module
        self.cp_all_data = copy.deepcopy(SubData.cp_all_data)
        self.cp_template_data = copy.deepcopy(SubData.cp_template_data)
        for chargepoint in self.cp_data:
            try:
                if "cp" in chargepoint:
                    self.cp_data[chargepoint].template = self.cp_template_data["cpt" + str(
                        self.cp_data[chargepoint].data.config.template)]
                    # Status zurücksetzen (wird jeden Zyklus neu ermittelt)
                    self.cp_data[chargepoint].data.get.state_str = None
            except Exception:
                log.exception("Fehler im Prepare-Modul für Ladepunkt "+str(chargepoint))

    def copy_module_data(self) -> None:
        with ModuleDataReceivedContext(self.event_module_update_completed):
            self.__copy_module_data()

    def __copy_module_data(self) -> None:
        """ kopiert die Daten, die per MQTT empfangen wurden.
        """
        try:
            self.__copy_counter_data()
            self.pv_data.clear()
            for pv in SubData.pv_data:
                stop = False
                for dev in SubData.system_data:
                    if "device" in dev:
                        for component in SubData.system_data[dev].components:
                            if component[9:] == pv[2:]:
                                self.pv_data[pv] = copy.deepcopy(SubData.pv_data[pv])
                                stop = True
                                break
                    if stop:
                        break
                self.pv_all_data = copy.deepcopy(SubData.pv_all_data)
            self.bat_data.clear()
            for bat in SubData.bat_data:
                stop = False
                for dev in SubData.system_data:
                    if "device" in dev:
                        for component in SubData.system_data[dev].components:
                            if component[9:] == bat[3:]:
                                self.bat_data[bat] = copy.deepcopy(SubData.bat_data[bat])
                                stop = True
                                break
                    if stop:
                        break
                self.bat_all_data = copy.deepcopy(SubData.bat_all_data)
        except Exception:
            log.exception("Fehler im Prepare-Modul")

    def copy_data(self) -> None:
        """ kopiert die Daten, die per MQTT empfangen wurden.
        """
        with ModuleDataReceivedContext(self.event_module_update_completed):
            try:
                self.general_data = copy.deepcopy(SubData.general_data)
                self.optional_data = copy.deepcopy(SubData.optional_data)
                self.__copy_ev_data()
                self.__copy_cp_data()
                self.__copy_counter_data()
                self.__copy_system_data()
                self.__copy_module_data()
                self.graph_data = copy.deepcopy(SubData.graph_data)
            except Exception:
                log.exception("Fehler im Prepare-Modul")

    def __copy_ev_data(self) -> None:
        self.ev_data.clear()
        for ev in SubData.ev_data:
            self.ev_data[ev] = copy.deepcopy(SubData.ev_data[ev])
        self.ev_template_data = copy.deepcopy(SubData.ev_template_data)
        self.ev_charge_template_data = copy.deepcopy(SubData.ev_charge_template_data)
        for vehicle in self.ev_data:
            try:
                self.ev_data[vehicle].charge_template = self.ev_charge_template_data["ct" + str(
                    self.ev_data[vehicle].data.charge_template)]
                # zuerst das aktuelle Profil laden
                self.ev_data[vehicle].ev_template = self.ev_template_data["et" + str(
                    self.ev_data[vehicle].data.ev_template)]
            except Exception:
                log.exception("Fehler im Prepare-Modul für EV "+str(vehicle))


class ModuleDataReceivedContext:
    """ Moduldaten erst kopieren, wenn alle Daten vom Broker empfangen wurden."""

    def __init__(self, event_module_update_completed):
        self.event_module_update_completed = event_module_update_completed

    def __enter__(self):
        global data
        try:
            timeout = data.general_data.data.control_interval/2
        except KeyError:
            timeout = 5
        if self.event_module_update_completed.wait(timeout) is False:
            log.error(
                "Modul-Daten wurden noch nicht vollständig empfangen. Timeout abgelaufen, fortsetzen der Regelung.")
        return None

    def __exit__(self, exception_type, exception, exception_traceback) -> bool:
        return True


data: Data


def data_init(event_module_update_completed: threading.Event):
    """instanziiert die Data-Klasse.
    """
    global data
    data = Data(event_module_update_completed)
