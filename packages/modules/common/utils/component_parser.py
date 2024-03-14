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
            for comp in item.components.values():
                if comp.component_config.id == id:
                    if f"device{item.device_config.id}" in not_finished_threads:
                        log.error(f"Keine aktuellen Werte für Gerät '{item.device_config.name}'"
                                  f"({item.device_config.id}) der Komponente '{comp.component_config.name}'"
                                  f"({comp.component_config.id}) verfügbar.")
                        return None
                    return comp
    else:
        log.error(f"Komponenten-ID '{id}' konnte nicht zugeordnet werden.")
        return None
