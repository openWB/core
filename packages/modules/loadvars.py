import logging
import threading
from typing import List

from control import data
from modules.utils import wait_for_module_update_completed
from modules.common.abstract_device import AbstractDevice
from modules.common.component_type import ComponentType, type_to_topic_mapping
from modules.common.store import update_values
from modules.common.utils.component_parser import get_component_obj_by_id
from helpermodules.utils import thread_handler

log = logging.getLogger(__name__)


class Loadvars:
    def __init__(self) -> None:
        self.event_module_update_completed = threading.Event()

    def get_values(self) -> None:
        topic = "openWB/set/system/device/module_update_completed"
        try:
            not_finished_threads = self._set_values()
            levels = data.data.counter_all_data.get_list_of_elements_per_level()
            levels.reverse()
            for level in levels:
                self._update_values_of_level(level, not_finished_threads)
                wait_for_module_update_completed(self.event_module_update_completed, topic)
                data.data.copy_module_data()
            wait_for_module_update_completed(self.event_module_update_completed, topic)
            thread_handler(self._get_general(), data.data.general_data.data.control_interval/3)
            thread_handler(self._set_general(), data.data.general_data.data.control_interval/3)
            wait_for_module_update_completed(self.event_module_update_completed, topic)
            data.data.pv_all_data.calc_power_for_all_components()
            data.data.bat_all_data.calc_power_for_all_components()
        except Exception:
            log.exception("Fehler im loadvars-Modul")

    def _set_values(self) -> List[str]:
        """Threads, um Werte von Geräten abzufragen"""
        modules_threads: List[threading.Thread] = []
        for item in data.data.system_data.values():
            try:
                if isinstance(item, AbstractDevice):
                    modules_threads.append(threading.Thread(target=item.update, args=(),
                                           name=f"device{item.device_config.id}"))
            except Exception:
                log.exception(f"Fehler im loadvars-Modul bei Element {item}")
        for cp in data.data.cp_data.values():
            try:
                modules_threads.append(threading.Thread(target=cp.chargepoint_module.get_values,
                                       args=(), name=f"set values cp{cp.chargepoint_module.config.id}"))
            except Exception:
                log.exception(f"Fehler im loadvars-Modul bei Element {cp.num}")
        return thread_handler(modules_threads, data.data.general_data.data.control_interval/3)

    def _update_values_of_level(self, elements, not_finished_threads: List[str]) -> None:
        """Threads, um von der niedrigsten Ebene der Hierarchie Werte ggf. miteinander zu verrechnen und zu
        veröffentlichen"""
        modules_threads: List[threading.Thread] = []
        for element in elements:
            try:
                if element["type"] == ComponentType.CHARGEPOINT.value:
                    chargepoint = data.data.cp_data[f'{type_to_topic_mapping(element["type"])}{element["id"]}']
                    if self.thread_without_set_value(modules_threads, not_finished_threads) is False:
                        modules_threads.append(threading.Thread(
                            target=update_values,
                            args=(chargepoint.chargepoint_module,),
                            name=f"update values cp{chargepoint.chargepoint_module.config.id}"))
                else:
                    component = get_component_obj_by_id(element["id"], not_finished_threads)
                    if component is None:
                        continue
                    modules_threads.append(threading.Thread(target=update_values, args=(
                        component,), name=f"component{component.component_config.id}"))
            except Exception:
                log.exception(f"Fehler im loadvars-Modul bei Element {element}")
        thread_handler(modules_threads, data.data.general_data.data.control_interval/3)

    def thread_without_set_value(self,
                                 modules_threads: List[threading.Thread],
                                 not_finished_threads: List[str]) -> bool:
        for t in not_finished_threads:
            for module_thread in modules_threads:
                if t == module_thread.name:
                    return True
        return False

    def _get_general(self) -> List[threading.Thread]:
        threads = []  # type: List[threading.Thread]
        try:
            # Beim ersten Durchlauf wird in jedem Fall eine Exception geworfen,
            # da die Daten erstmalig ins data-Modul kopiert werden müssen.
            if data.data.general_data.data.ripple_control_receiver.module:
                threads.append(
                    threading.Thread(target=data.data.general_data.data.ripple_control_receiver.module.update,
                                     args=(), name="get ripple control receiver"))
        except Exception:
            log.exception("Fehler im loadvars-Modul")
        finally:
            return threads

    def _set_general(self) -> List[threading.Thread]:
        threads = []  # type: List[threading.Thread]
        try:
            if data.data.general_data.data.ripple_control_receiver.module:
                threads.append(threading.Thread(target=update_values,
                               args=(data.data.general_data.data.ripple_control_receiver.module,),
                               name="set ripple control receiver"))
        except Exception:
            log.exception("Fehler im loadvars-Modul")
        finally:
            return threads
