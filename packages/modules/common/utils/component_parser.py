import logging
from typing import Any, List, Optional

from control import data
from modules.common.abstract_device import AbstractDevice
log = logging.getLogger(__name__)


def get_component_name_by_id(id: int):
    for item in data.data.system_data.values():
        if isinstance(item, AbstractDevice):
            for comp in item.components.values():
                if comp.component_config.id == id:
                    return comp.component_config.name
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
                    return comp
    else:
        log.error(f"Element {id} konnte keinem Gerät zugeordnet werden.")
        return None
