#!/usr/bin/env python3


try:
    from ..common import modbus
    from ..common.abstract_component import AbstractComponent, ComponentUpdater
    from ..common.component_state import InverterState
    from ..common.module_error import ComponentInfo
    from ..common.store import get_inverter_value_store
except (ImportError, ValueError):
    from modules.common import modbus
    from ..common.abstract_component import AbstractComponent, ComponentUpdater
    from ..common.component_state import InverterState
    from ..common.module_error import ComponentInfo
    from ..common.store import get_inverter_value_store


def get_default_config() -> dict:
    return {
        "name": "MQTT-Wechselrichter",
        "type": "inverter",
        "id": None,
        "configuration": {
        }
    }


def create_component(device_config: dict, component_config: dict,
                     modbus_client):
    return ComponentUpdater(
        MqttInverter(
            device_config["id"],
            component_config,
            modbus_client,
        ), get_inverter_value_store(component_config["id"]))


class MqttInverter(AbstractComponent[InverterState]):
    def __init__(self, device_id: int, component_config: dict,
                 tcp_client: modbus.ModbusClient) -> None:
        self.component_config = component_config

    def get_component_info(self) -> ComponentInfo:
        return ComponentInfo(self.component_config["id"],
                             self.component_config["type"],
                             self.component_config["name"])

    def get_values(self) -> InverterState:
        """ liest die Werte des Moduls aus.
        """
        pass
        counter_state = InverterState(counter=0, power=0)
        return counter_state
