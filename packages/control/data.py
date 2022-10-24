""" Verschachtelte Listen, die die Daten zur Berechnung des Algorithmus enthalten.
Dictionary: Zugriff erfolgt bei Dictionary über Keys, nicht über Indizes wie bei Listen. Das hat den Vorteil, dass
Instanzen gelöscht werden können, der Zugriff aber nicht verändert werden muss.
"""
import copy
import logging
import threading
from typing import Dict
from control.chargepoint import AllChargepoints, Chargepoint

import dataclass_utils
from helpermodules.subdata import SubData
from control.ev import ChargeTemplate, Ev, EvTemplate
from control.general import General
from control.optional import Optional
from modules.common.abstract_device import AbstractDevice

log = logging.getLogger(__name__)


class Data:
    def __init__(self, event_module_update_completed: threading.Event):
        self.event_module_update_completed = event_module_update_completed
        self.event = threading.Event()
        self.event.set()
        self._bat_data = {}
        self._bat_module_data = {}
        self._counter_data = {}
        self._counter_module_data = {}
        self._cp_data = {}
        self._cp_all_data = AllChargepoints()
        self._cp_template_data = {}
        self._ev_charge_template_data = {}
        self._ev_data = {}
        self._ev_template_data = {}
        self._general_data = General()
        self._graph_data = {}
        self._optional_data = Optional()
        self._pv_data = {}
        self._system_data = {}

    # getter-Funktion, der Zugriff erfolgt wie bei einem Zugriff auf eine öffentliche Variable.
    @property
    def bat_data(self):
        """ gibt die Variable zurück. Durch das Event wird verhindert, das gleichzeitig geschrieben und gelesen wird.

        Return
        ------
        temp: Variable
        """
        self.event.wait()
        self.event.clear()
        temp = self._bat_data
        self.event.set()
        return temp

    @bat_data.setter
    def bat_data(self, value):
        """ setzt die Variable. Durch das Event wird verhindert, das gleichzeitig geschrieben und gelesen wird.

        Parameter
        ---------
        value: Wert, der gesetzt werden soll.
        """
        self.event.wait()
        self.event.clear()
        self._bat_data = value
        self.event.set()

    @property
    def graph_data(self):
        self.event.wait()
        self.event.clear()
        temp = self._graph_data
        self.event.set()
        return temp

    @graph_data.setter
    def graph_data(self, value):
        self.event.wait()
        self.event.clear()
        self._graph_data = value
        self.event.set()

    @property
    def counter_data(self):
        self.event.wait()
        self.event.clear()
        temp = self._counter_data
        self.event.set()
        return temp

    @counter_data.setter
    def counter_data(self, value):
        self.event.wait()
        self.event.clear()
        self._counter_data = value
        self.event.set()

    @property
    def counter_module_data(self):
        self.event.wait()
        self.event.clear()
        temp = self._counter_module_data
        self.event.set()
        return temp

    @counter_module_data.setter
    def counter_module_data(self, value):
        self.event.wait()
        self.event.clear()
        self._counter_module_data = value
        self.event.set()

    @property
    def cp_data(self) -> Dict[str, Chargepoint]:
        self.event.wait()
        self.event.clear()
        temp = self._cp_data
        self.event.set()
        return temp

    @cp_data.setter
    def cp_data(self, value):
        self.event.wait()
        self.event.clear()
        self._cp_data = value
        self.event.set()

    @property
    def cp_all_data(self) -> AllChargepoints:
        self.event.wait()
        self.event.clear()
        temp = self._cp_all_data
        self.event.set()
        return temp

    @cp_all_data.setter
    def cp_all_data(self, value):
        self.event.wait()
        self.event.clear()
        self._cp_all_data = value
        self.event.set()

    @property
    def cp_template_data(self):
        self.event.wait()
        self.event.clear()
        temp = self._cp_template_data
        self.event.set()
        return temp

    @cp_template_data.setter
    def cp_template_data(self, value):
        self.event.wait()
        self.event.clear()
        self._cp_template_data = value
        self.event.set()

    @property
    def ev_charge_template_data(self) -> Dict[str, ChargeTemplate]:
        self.event.wait()
        self.event.clear()
        temp = self._ev_charge_template_data
        self.event.set()
        return temp

    @ev_charge_template_data.setter
    def ev_charge_template_data(self, value):
        self.event.wait()
        self.event.clear()
        self._ev_charge_template_data = value
        self.event.set()

    @property
    def ev_data(self) -> Dict[str, Ev]:
        self.event.wait()
        self.event.clear()
        temp = self._ev_data
        self.event.set()
        return temp

    @ev_data.setter
    def ev_data(self, value):
        self.event.wait()
        self.event.clear()
        self._ev_data = value
        self.event.set()

    @property
    def ev_template_data(self) -> Dict[str, EvTemplate]:
        self.event.wait()
        self.event.clear()
        temp = self._ev_template_data
        self.event.set()
        return temp

    @ev_template_data .setter
    def ev_template_data(self, value):
        self.event.wait()
        self.event.clear()
        self._ev_template_data = value
        self.event.set()

    @property
    def general_data(self) -> General:
        self.event.wait()
        self.event.clear()
        temp = self._general_data
        self.event.set()
        return temp

    @general_data.setter
    def general_data(self, value):
        self.event.wait()
        self.event.clear()
        self._general_data = value
        self.event.set()

    @property
    def optional_data(self) -> Optional:
        self.event.wait()
        self.event.clear()
        temp = self._optional_data
        self.event.set()
        return temp

    @optional_data.setter
    def optional_data(self, value):
        self.event.wait()
        self.event.clear()
        self._optional_data = value
        self.event.set()

    @property
    def pv_data(self):
        self.event.wait()
        self.event.clear()
        temp = self._pv_data
        self.event.set()
        return temp

    @pv_data.setter
    def pv_data(self, value):
        self.event.wait()
        self.event.clear()
        self._pv_data = value
        self.event.set()

    @property
    def system_data(self):
        self.event.wait()
        self.event.clear()
        temp = self._system_data
        self.event.set()
        return temp

    @system_data.setter
    def system_data(self, value):
        self.event.wait()
        self.event.clear()
        self._system_data = value
        self.event.set()

    def print_all(self):
        self._print_dictionaries(self._bat_data)
        self._print_dictionaries(self._bat_module_data)
        log.debug(f"cp_all_data\n{self._cp_all_data.data}")
        self._print_dictionaries(self._cp_data)
        self._print_dictionaries(self._cp_template_data)
        self._print_dictionaries(self._counter_data)
        self._print_dictionaries(self._counter_module_data)
        self._print_dictionaries(self._ev_charge_template_data)
        self._print_dictionaries(self._ev_data)
        self._print_dictionaries(self._ev_template_data)
        log.debug(f"general_data\n{self._general_data.data}")
        self._print_dictionaries(self._graph_data)
        log.debug(f"optional_data\n{self._optional_data.data}")
        self._print_dictionaries(self._pv_data)
        self._print_dictionaries(self._system_data)
        self._print_device_config(self._system_data)
        log.debug("\n")

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
                        log.debug(key+"\n"+str(data[key].data))
                    except AttributeError:
                        # Devices haben kein data-Dict
                        pass
                else:
                    log.debug(key+"\n"+"Klasse fehlt")
            except Exception:
                log.exception("Fehler im Data-Modul")

    def _print_device_config(self, data: Dict[str, AbstractDevice]):
        for key, value in data.items():
            try:
                if isinstance(value, AbstractDevice):
                    log.debug(f"{key}\n{dataclass_utils.asdict(value.device_config)}")
                    for comp_key, comp_value in value.components.items():
                        log.debug(f"{comp_key}\n{dataclass_utils.asdict(comp_value.component_config)}")
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
            # Bei einer Neukonfiguration eines Device/Komponente wird dieses Neuinitialisiert. Nur bei Komponenten
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
            self.cp_data[cp] = copy.deepcopy(SubData.cp_data[cp].chargepoint)
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
                if pv != "all":
                    for dev in SubData.system_data:
                        if "device" in dev:
                            for component in SubData.system_data[dev].components:
                                if component[9:] == pv[2:]:
                                    self.pv_data[pv] = copy.deepcopy(SubData.pv_data[pv])
                                    stop = True
                                    break
                        if stop:
                            break
                else:
                    self.pv_data[pv] = copy.deepcopy(SubData.pv_data[pv])
            self.bat_data.clear()
            for bat in SubData.bat_data:
                stop = False
                if bat != "all":
                    for dev in SubData.system_data:
                        if "device" in dev:
                            for component in SubData.system_data[dev].components:
                                if component[9:] == bat[3:]:
                                    self.bat_data[bat] = copy.deepcopy(SubData.bat_data[bat])
                                    stop = True
                                    break
                        if stop:
                            break
                else:
                    self.bat_data[bat] = copy.deepcopy(SubData.bat_data[bat])
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
                # Globaler oder individueller Lademodus?
                if self.general_data.data.chargemode_config.individual_mode:
                    self.ev_data[vehicle].charge_template = self.ev_charge_template_data["ct" + str(
                        self.ev_data[vehicle].data.charge_template)]
                else:
                    self.ev_data[vehicle].charge_template = self.ev_charge_template_data["ct0"]
                # zuerst das aktuelle Template laden
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
