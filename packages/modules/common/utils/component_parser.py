import logging
from typing import Any, List, Optional

from control import data
from modules.common.abstract_device import AbstractDevice
from modules.common.abstract_io import AbstractIo
from modules.common.component_type import type_to_topic_mapping
log = logging.getLogger(__name__)


def get_component_name_by_id(id: int):
    for item in data.data.system_data.values():
        if isinstance(item, AbstractDevice):
            for comp in item.components.values():
                if comp.component_config.id == id:
                    return comp.component_config.name
    else:
        raise ValueError(f"Element {id} konnte keinem Gerät zugeordnet werden.")


def get_io_name_by_id(id: int):
    for item in data.data.system_data.values():
        if isinstance(item, AbstractIo):
            if item.config.id == id:
                return item.config.name
    else:
        raise ValueError(f"Element {id} konnte keinem Gerät zugeordnet werden.")


def get_component_obj_by_id(id: int, not_finished_threads: List[str]) -> Optional[Any]:
    for item in data.data.system_data.values():
        if isinstance(item, AbstractDevice):
            for t in not_finished_threads:
                if t == f"device{item.device_config.id}":
                    log.error(f"Keine aktuellen Werte für Gerät {item.device_config.name}")
                    return None
            for comp in item.components.values():
                if comp.component_config.id == id:
                    for type in ["bat", "counter", "inverter"]:
                        if type in comp.component_config.type:
                            module_data = getattr(data.data, f"{type_to_topic_mapping(type)}_data")
                            if module_data[f"{type_to_topic_mapping(type)}{id}"].data.get.fault_state == 2:
                                log.error(f"Fehlerstatus in Komponente {comp.component_config.name}. "
                                          "Werte werden nicht aktualisiert.")
                                return None
                            else:
                                return comp
    else:
        log.error(f"Element {id} konnte keinem Gerät zugeordnet werden.")
        return None
