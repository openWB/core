#!/usr/bin/env python3

from modules.common import modbus
from modules.common.abstract_component import AbstractComponent, ComponentUpdater
from modules.common.component_state import BatState
from modules.common.module_error import ComponentInfo
from modules.common.store import get_bat_value_store


def get_default_config() -> dict:
    return {
        "name": "MQTT-Speicher",
        "type": "bat",
        "id": None,
        "configuration": {
        }
    }


def create_component(device_config: dict, component_config: dict,
                     modbus_client):
    return ComponentUpdater(
        MqttBat(
            device_config["id"],
            component_config,
            modbus_client,
        ), get_bat_value_store(component_config["id"]))


class MqttBat(AbstractComponent[BatState]):
    def __init__(self, device_id: int, component_config: dict,
                 tcp_client: modbus.ModbusClient) -> None:
        self.component_config = component_config

    def get_component_info(self) -> ComponentInfo:
        return ComponentInfo(self.component_config["id"],
                             self.component_config["name"],
                             self.component_config["type"])

    def get_values(self) -> BatState:
        """ liest die Werte des Moduls aus.
        """
        counter_state = BatState(imported=0, exported=0, power=0, soc=0)
        return counter_state
