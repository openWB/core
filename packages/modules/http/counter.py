#!/usr/bin/env python3
from modules.common.component_state import CounterState
from modules.common.fault_state import ComponentInfo
from modules.common.store import get_counter_value_store
from modules.http.api import create_request_function


def get_default_config() -> dict:
    return {
        "name": "HTTP Zähler",
        "id": 0,
        "type": "counter",
        "configuration": {
            "power_path": "",
            "imported_path": "none",
            "exported_path": "none",
            "current_l1_path": "none",
            "current_l2_path": "none",
            "current_l3_path": "none",
        }
    }


class HttpCounter:
    def __init__(self, component_config: dict, domain: str) -> None:
        self.__get_power = create_request_function(domain, component_config["configuration"]["power_path"])
        self.__get_imported = create_request_function(domain, component_config["configuration"]["imported_path"])
        self.__get_exported = create_request_function(domain, component_config["configuration"]["exported_path"])
        self.__get_currents = [
            create_request_function(domain,
                                    component_config["configuration"]["current_l" + str(i) + "_path"])
            for i in range(1, 4)
        ]

        self.component_config = component_config
        self.__store = get_counter_value_store(component_config["id"])
        self.component_info = ComponentInfo.from_component_config(component_config)

    def update(self):
        counter_state = CounterState(
            currents=[getter() for getter in self.__get_currents],
            imported=self.__get_imported(),
            exported=self.__get_exported(),
            power=self.__get_power()
        )
        self.__store.set(counter_state)
