#!/usr/bin/env python3
import logging
from modules.common.abstract_device import AbstractDevice
from modules.common.component_context import MultiComponentUpdateContext
from modules.mqtt import bat
from modules.mqtt import counter
from modules.mqtt import inverter

log = logging.getLogger(__name__)


def get_default_config() -> dict:
    return {
        "name": "MQTT",
        "type": "mqtt",
        "id": None,
        "configuration": {}
    }


class Device(AbstractDevice):
    COMPONENT_TYPE_TO_CLASS = {
        "bat": bat.MqttBat,
        "counter": counter.MqttCounter,
        "inverter": inverter.MqttInverter
    }

    def __init__(self, device_config: dict) -> None:
        self.components = {}
        try:
            self.device_config = device_config
        except Exception:
            log.exception("Fehler im Modul " + device_config["name"])

    def add_component(self, component_config: dict) -> None:
        component_type = component_config["type"]
        if component_type in self.COMPONENT_TYPE_TO_CLASS:
            self.components["component"+str(component_config["id"])
                            ] = (self.COMPONENT_TYPE_TO_CLASS[component_type](component_config))

    def update(self) -> None:
        if self.components:
            with MultiComponentUpdateContext(self.components):
                log.debug("MQTT-Module müssen nicht ausgelesen werden.")
        else:
            log.warning(
                self.device_config["name"] +
                ": Es konnten keine Werte gelesen werden, da noch keine Komponenten konfiguriert wurden."
            )
