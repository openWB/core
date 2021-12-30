#!/usr/bin/env python3
from modules.common.fault_state import ComponentInfo


def get_default_config() -> dict:
    return {
        "name": "MQTT-Speicher",
        "type": "bat",
        "id": None,
        "configuration": {
        }
    }


class MqttBat:
    def __init__(self, component_config: dict) -> None:
        self.component_info = ComponentInfo.from_component_config(component_config)
