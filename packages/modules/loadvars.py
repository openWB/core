import logging
import threading
from typing import List

from control import data
from modules import ripple_control_receiver
from modules.common.abstract_device import AbstractDevice
from modules.common.component_type import ComponentType, type_to_topic_mapping
from modules.common.store import update_values
from helpermodules import pub
from helpermodules.utils import thread_handler

log = logging.getLogger(__name__)


class Loadvars:
    def __init__(self) -> None:
        self.event_module_update_completed = threading.Event()

    def get_values(self) -> None:
        try:
            self._set_values()
            levels = data.data.counter_all_data.get_list_of_elements_per_level()
            levels.reverse()
            for level in levels:
                with ModuleUpdateCompletedContext(self.event_module_update_completed):
                    self._update_values_of_level(level)
                data.data.copy_module_data()
            with ModuleUpdateCompletedContext(self.event_module_update_completed):
                thread_handler(self._get_general())
            data.data.pv_data["all"].calc_power_for_all_components()
            data.data.bat_data["all"].calc_power_for_all_components()
        except Exception:
            log.exception("Fehler im loadvars-Modul")

    def _set_values(self) -> None:
        """Threads, um Werte von Geräten abzufragen"""
        modules_threads: List[threading.Thread] = []
        for item in data.data.system_data.values():
            try:
                if isinstance(item, AbstractDevice):
                    modules_threads.append(threading.Thread(target=item.update, args=()))
            except Exception:
                log.exception(f"Fehler im loadvars-Modul bei Element {item}")
        for cp in data.data.cp_data.values():
            try:
                modules_threads.append(threading.Thread(target=cp.chargepoint_module.get_values, args=()))
            except Exception:
                log.exception(f"Fehler im loadvars-Modul bei Element {cp.num}")
        thread_handler(modules_threads)

    def _update_values_of_level(self, elements) -> None:
        """Threads, um von der niedrigsten Ebene der Hierarchie Werte ggf. miteinander zu verrechnen und zu publishen"""
        modules_threads: List[threading.Thread] = []
        for element in elements:
            try:
                if element["type"] == ComponentType.CHARGEPOINT.value:
                    chargepoint = data.data.cp_data[f'{type_to_topic_mapping(element["type"])}{element["id"]}']
                    modules_threads.append(threading.Thread(
                        target=update_values, args=(chargepoint.chargepoint_module,)))
                else:
                    component = self.__get_component_obj_by_id(element["id"])
                    if component is None:
                        continue
                    modules_threads.append(threading.Thread(target=update_values, args=(component,)))
            except Exception:
                log.exception(f"Fehler im loadvars-Modul bei Element {element}")
        thread_handler(modules_threads)

    def __get_component_obj_by_id(self, id: int):
        for item in data.data.system_data.values():
            if isinstance(item, AbstractDevice):
                for comp in item.components.values():
                    if comp.component_config.id == id:
                        return comp
        else:
            log.error(f"Element {id} konnte keinem Gerät zugeordnet werden.")
            return None

    def _get_general(self) -> List[threading.Thread]:
        threads = []  # type: List[threading.Thread]
        try:
            # Beim ersten Durchlauf wird in jedem Fall eine Exception geworfen,
            # da die Daten erstmalig ins data-Modul kopiert werden müssen.
            if data.data.general_data.data.ripple_control_receiver.configured:
                threads.append(threading.Thread(target=ripple_control_receiver.read, args=()))
        except Exception:
            log.exception("Fehler im loadvars-Modul")
        finally:
            return threads


class ModuleUpdateCompletedContext:
    def __init__(self, event_module_update_completed: threading.Event):
        self.event_module_update_completed = event_module_update_completed

    def __enter__(self):
        timeout = data.data.general_data.data.control_interval/2
        if self.event_module_update_completed.wait(timeout) is False:
            log.error(
                "Modul-Daten wurden noch nicht vollständig empfangen. Timeout abgelaufen, fortsetzen der Regelung.")
        return None

    def __exit__(self, exception_type, exception, exception_traceback) -> bool:
        self.event_module_update_completed.clear()
        pub.Pub().pub("openWB/set/system/device/module_update_completed", True)
        return True
