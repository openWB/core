import logging
import threading
from typing import Callable, List

from control import data
from modules import ripple_control_receiver
from helpermodules import pub

log = logging.getLogger(__name__)


class Loadvars:
    def __init__(self) -> None:
        self.event_module_update_completed = threading.Event()

    def get_hardware_values(self):
        with ModuleUpdateCompletedContext(self.event_module_update_completed):
            self.__get_values([self._get_cp, self._get_general, self._get_modules])
            data.data.pv_data["all"].calc_power_for_all_components()
            data.data.bat_data["all"].calc_power_for_all_components()

    def get_virtual_values(self):
        """ Virtuelle Module ermitteln die Werte rechnerisch auf Basis der Messwerte anderer Module.
        Daher können sie erst die Werte ermitteln, wenn die physischen Module ihre Werte ermittelt haben.
        Würde man alle Module parallel abfragen, wären die virtuellen Module immer einen Zyklus hinterher.
        """
        with ModuleUpdateCompletedContext(self.event_module_update_completed):
            self.__get_values([self._get_virtual_counters])
            data.data.pv_data["all"].calc_power_for_all_components()
            data.data.bat_data["all"].calc_power_for_all_components()

    def __get_values(self, value_functions: List[Callable]):
        try:
            threads = []
            for func in value_functions:
                threads.extend(func())
            # Start them all
            if threads:
                for thread in threads:
                    thread.start()

                # Wait for all to complete
                for thread in threads:
                    thread.join(timeout=data.data.general_data["general"].data["control_interval"]/3)

                for thread in threads:
                    if thread.is_alive():
                        log.error(
                            thread.name +
                            " konnte nicht innerhalb des Timeouts die Werte abfragen, die abgefragten Werte werden" +
                            " nicht in der Regelung verwendet.")
        except Exception:
            log.exception("Fehler im loadvars-Modul")

    def _get_virtual_counters(self):
        """ vorhandene Zähler durchgehen und je nach Konfiguration Module zur Abfrage der Werte aufrufen
        """
        modules_threads = []  # type: List[threading.Thread]
        try:
            for item in data.data.system_data:
                try:
                    if "device" in item:
                        try:
                            type = data.data.system_data[item].device_config.type
                        except AttributeError:
                            type = data.data.system_data[item].device_config["type"]
                        if type == "virtual":
                            thread = None
                            module = data.data.system_data[item]
                            thread = threading.Thread(target=module.get_values, args=())
                            if thread is not None:
                                modules_threads.append(thread)
                except Exception:
                    log.exception("Fehler im loadvars-Modul")
            return modules_threads
        except Exception:
            log.exception("Fehler im loadvars-Modul")
        finally:
            return modules_threads

    def _get_cp(self) -> List[threading.Thread]:
        modules_threads = []  # type: List[threading.Thread]
        try:
            for item in data.data.cp_data:
                try:
                    if "cp" in item:
                        thread = None
                        chargepoint_module = data.data.cp_data[item].chargepoint_module
                        thread = threading.Thread(target=chargepoint_module.get_values, args=())
                        if thread is not None:
                            modules_threads.append(thread)
                except Exception:
                    log.exception("Fehler im loadvars-Modul")
        except Exception:
            log.exception("Fehler im loadvars-Modul")
        finally:
            return modules_threads

    def _get_general(self) -> List[threading.Thread]:
        threads = []  # type: List[threading.Thread]
        try:
            # Beim ersten Durchlauf wird in jedem Fall eine Exception geworfen,
            # da die Daten erstmalig ins data-Modul kopiert werden müssen.
            if data.data.general_data["general"].data[
                    "ripple_control_receiver"]["configured"]:
                threads.append(threading.Thread(target=ripple_control_receiver.read, args=()))
        except Exception:
            log.exception("Fehler im loadvars-Modul")
        finally:
            return threads

    def _get_modules(self) -> List[threading.Thread]:
        modules_threads = []  # type: List[threading.Thread]
        try:
            for item in data.data.system_data:
                try:
                    if "device" in item:
                        try:
                            type = data.data.system_data[item].device_config.type
                        except AttributeError:
                            type = data.data.system_data[item].device_config["type"]
                        if type != "virtual":
                            thread = None
                            module = data.data.system_data[item]
                            thread = threading.Thread(target=module.update, args=())
                            if thread is not None:
                                modules_threads.append(thread)
                except Exception:
                    log.exception("Fehler im loadvars-Modul")
            return modules_threads
        except Exception:
            log.exception("Fehler im loadvars-Modul")
        finally:
            return modules_threads


class ModuleUpdateCompletedContext:
    def __init__(self, event_module_update_completed):
        self.event_module_update_completed = event_module_update_completed

    def __enter__(self):
        timeout = data.data.general_data["general"].data["control_interval"]/2
        if self.event_module_update_completed.wait(timeout) is False:
            log.error(
                "Modul-Daten wurden noch nicht vollständig empfangen. Timeout abgelaufen, fortsetzen der Regelung.")
        return None

    def __exit__(self, exception_type, exception, exception_traceback) -> bool:
        self.event_module_update_completed.clear()
        pub.Pub().pub("openWB/set/system/device/module_update_completed", True)
        return True
