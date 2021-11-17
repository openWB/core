#!/usr/bin/env python3
try:
    from ..common import modbus
    from ..common.abstract_component import AbstractComponent, ComponentUpdater
    from ..common.component_state import CounterState
    from ..common.module_error import ComponentInfo
    from ..common.store import get_counter_value_store
except (ImportError, ValueError, SystemError):
    from modules.common import modbus
    from modules.common.abstract_component import AbstractComponent, ComponentUpdater
    from modules.common.component_state import CounterState
    from modules.common.module_error import ComponentInfo
    from modules.common.store import get_counter_value_store


def get_default_config() -> dict:
    return {
        "name": "MQTT-Zähler",
        "type": "counter",
        "id": None,
        "configuration": {
        }
    }


def create_component(device_config: dict, component_config: dict,
                     modbus_client):
    return ComponentUpdater(
        MqttCounter(
            device_config["id"],
            component_config,
            modbus_client,
        ), get_counter_value_store(component_config["id"]))


class MqttCounter(AbstractComponent[CounterState]):
    def __init__(self, device_id: int, component_config: dict,
                 tcp_client: modbus.ModbusClient) -> None:
        self.component_config = component_config

    def get_component_info(self) -> ComponentInfo:
        return ComponentInfo(self.component_config["id"],
                             self.component_config["type"],
                             self.component_config["name"])

    def get_values(self) -> CounterState:
        """ liest die Werte des Moduls aus.
        """
        pass
        counter_state = CounterState(imported=0, exported=0, power_all=0)
        return counter_state
