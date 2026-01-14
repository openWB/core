import logging
from threading import Event, Thread
from typing import List

from control import data
from modules.common.abstract_io import AbstractIoDevice
from modules.common.store._tariff import get_price_value_store
from modules.utils import wait_for_module_update_completed
from modules.common.abstract_device import AbstractDevice
from modules.common.component_type import ComponentType, type_to_topic_mapping
from modules.common.store import update_values
from modules.common.utils.component_parser import get_finished_component_obj_by_id
from helpermodules.utils import joined_thread_handler
from helpermodules.constants import NO_ERROR
from helpermodules.pub import Pub

log = logging.getLogger(__name__)


class Loadvars:
    def __init__(self) -> None:
        self.event_module_update_completed = Event()
        self.price_value_store = get_price_value_store()

    def get_values(self) -> None:
        topic = "openWB/set/system/device/module_update_completed"
        try:
            not_finished_threads = self._set_values()
            levels = data.data.counter_all_data.get_list_of_elements_per_level()
            levels.reverse()
            for level in levels:
                self._update_values_of_level_buttom_top(level, not_finished_threads)
                wait_for_module_update_completed(self.event_module_update_completed, topic)
                data.data.copy_module_data()
            self._update_values_virtual_counter_uncounted_consumption(not_finished_threads)
            wait_for_module_update_completed(self.event_module_update_completed, topic)
            data.data.copy_module_data()
            wait_for_module_update_completed(self.event_module_update_completed, topic)
            joined_thread_handler(self._get_io(), data.data.general_data.data.control_interval/3)
            joined_thread_handler(self._set_io(), data.data.general_data.data.control_interval/3)
            wait_for_module_update_completed(self.event_module_update_completed, topic)
            if data.data.optional_data.data.electricity_pricing.get.next_query_time is None:
                self.ep_get_prices()
        except Exception:
            log.exception("Fehler im loadvars-Modul")

    def _set_values(self) -> List[str]:
        """Threads, um Werte von Geräten abzufragen"""
        modules_threads: List[Thread] = []
        for item in data.data.system_data.values():
            try:
                if isinstance(item, AbstractDevice):
                    modules_threads.append(Thread(target=item.update, args=(),
                                           name=f"device{item.device_config.id}"))
            except Exception:
                log.exception(f"Fehler im loadvars-Modul bei Element {item}")
        for cp in data.data.cp_data.values():
            try:
                modules_threads.append(Thread(target=cp.chargepoint_module.get_values,
                                       args=(), name=f"set values cp{cp.chargepoint_module.config.id}"))
            except Exception:
                log.exception(f"Fehler im loadvars-Modul bei Element {cp.num}")
        for consumer in data.data.consumer_data.values():
            try:
                if consumer.extra_meter is not None:
                    modules_threads.append(Thread(
                        target=consumer.extra_meter.update,
                        args=(),
                        name=f"set values consumer{consumer.num}_extra_meter_device"))
                else:
                    modules_threads.append(Thread(target=consumer.module.update,
                                                  args=(), name=f"set values consumer{consumer.data.module.id}"))
            except Exception:
                log.exception(f"Fehler im loadvars-Modul bei Element {consumer.num}")
        return joined_thread_handler(modules_threads, data.data.general_data.data.control_interval/3)

    def _update_values_of_level_buttom_top(self, elements, not_finished_threads: List[str]) -> None:
        """Threads, um von der niedrigsten Ebene der Hierarchie beginnend Werte ggf. miteinander zu verrechnen und zu
        veröffentlichen"""
        modules_threads: List[Thread] = []
        for element in elements:
            try:
                if element["type"] == ComponentType.CHARGEPOINT.value:
                    chargepoint = data.data.cp_data[f'{type_to_topic_mapping(element["type"])}{element["id"]}']
                    thread_name = f"set values cp{chargepoint.chargepoint_module.config.id}"
                    if thread_name not in not_finished_threads:
                        modules_threads.append(Thread(
                            target=update_values,
                            args=(chargepoint.chargepoint_module,),
                            name=f"update values cp{chargepoint.chargepoint_module.config.id}"))
                elif element["type"] == ComponentType.CONSUMER.value:
                    consumer = data.data.consumer_data[f'{type_to_topic_mapping(element["type"])}{element["id"]}']
                    if consumer.extra_meter is not None:
                        thread_name = f"set values cp{chargepoint.chargepoint_module.config.id}"
                        if thread_name not in not_finished_threads:
                            modules_threads.append(Thread(
                                target=update_values,
                                args=(consumer.extra_meter.component["componentNone"],),
                                name=f"set values consumer{consumer.num}_extra_meter_device"))
                        else:
                            modules_threads.append(Thread(
                                target=update_values,
                                args=(consumer,),
                                name=f"set values consumer{consumer.data.module.id}"))
                else:
                    component = get_finished_component_obj_by_id(element["id"], not_finished_threads)
                    if component is None:
                        continue
                    modules_threads.append(Thread(target=update_values, args=(
                        component,), name=f"component{component.component_config.id}"))
            except Exception:
                log.exception(f"Fehler im loadvars-Modul bei Element {element}")
        joined_thread_handler(modules_threads, data.data.general_data.data.control_interval/3)

    def _update_values_virtual_counter_uncounted_consumption(self, not_finished_threads: List[str]) -> None:
        modules_threads: List[Thread] = []
        for counter in data.data.counter_data.values():
            try:
                component = get_finished_component_obj_by_id(counter.num, not_finished_threads)
                if component.component_config.type == "virtual":
                    if len(data.data.counter_all_data.get_entry_of_element(counter.num)["children"]) == 0:
                        thread_name = f"component{component.component_config.id}"
                        if thread_name not in not_finished_threads:
                            modules_threads.append(Thread(
                                target=update_values,
                                args=(component,),
                                name=f"component{component.component_config.id}"))
            except Exception:
                log.exception(f"Fehler im loadvars-Modul bei Zähler {counter}")
        joined_thread_handler(modules_threads, data.data.general_data.data.control_interval/3)

    def _get_io(self) -> List[Thread]:
        threads = []  # type: List[Thread]
        try:
            for io_device in data.data.system_data.values():
                try:
                    if isinstance(io_device, AbstractIoDevice):
                        threads.append(
                            Thread(target=io_device.read, args=(), name="get io state"))
                except Exception:
                    log.exception("Fehler im loadvars-Modul")
        except Exception:
            log.exception("Fehler im loadvars-Modul")
        finally:
            return threads

    def _set_io(self) -> List[Thread]:
        threads = []  # type: List[Thread]
        try:
            for io_device in data.data.system_data.values():
                try:
                    if isinstance(io_device, AbstractIoDevice):
                        threads.append(Thread(target=update_values, args=(io_device,), name="publish io state"))
                except Exception:
                    log.exception("Fehler im loadvars-Modul")
        except Exception:
            log.exception("Fehler im loadvars-Modul")
        finally:
            return threads

    def ep_get_prices(self):
        def append_thread_set_values(module_name: str) -> None:
            module = getattr(data.data.optional_data, f"{module_name}_module")
            if module:
                threads_set_values.append(Thread(target=module.update, args=(),
                                          name=f"update values {module_name}_module"))
            else:
                # Wenn kein Modul konfiguriert ist, Fehlerstatus zurücksetzen.
                module_data = getattr(data.data.optional_data.data.electricity_pricing, f"{module_name}")
                if (module_data.get.fault_state != 0 or module_data.get.fault_str != NO_ERROR):
                    module_data.get.fault_state = 0
                    module_data.get.fault_str = NO_ERROR
                    Pub().pub(f"openWB/set/optional/ep/{module_name}/get/fault_state", 0)
                    Pub().pub(f"openWB/set/optional/ep/{module_name}/get/fault_str", NO_ERROR)

        try:
            if data.data.optional_data.et_price_update_required():
                threads_set_values = []
                append_thread_set_values("flexible_tariff")
                append_thread_set_values("grid_fee")
                joined_thread_handler(threads_set_values, None)
                wait_for_module_update_completed(self.event_module_update_completed,
                                                 "openWB/set/optional/ep/module_update_completed")
                data.data.copy_data()
                self.price_value_store.update()
        except Exception as e:
            log.exception("Fehler im Optional-Modul: %s", e)
