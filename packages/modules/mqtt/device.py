#!/usr/bin/env python3
from helpermodules.log import MainLogger
from modules.common.abstract_device import AbstractDevice
from modules.common.component_context import MultiComponentUpdateContext
from modules.mqtt import bat
from modules.mqtt import counter
from modules.mqtt import inverter


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
        self._components = {}
        try:
            self.device_config = device_config
        except Exception:
            MainLogger().exception("Fehler im Modul " + device_config["name"])

    def add_component(self, component_config: dict) -> None:
        component_type = component_config["type"]
        if component_type in self.COMPONENT_TYPE_TO_CLASS:
            self._components["component"+str(component_config["id"])
                             ] = (self.COMPONENT_TYPE_TO_CLASS[component_type](component_config))

    def update(self) -> None:
        if self._components:
            with MultiComponentUpdateContext(self._components):
                MainLogger().debug("MQTT-Module müssen nicht ausgelesen werden.")
        else:
            MainLogger().warning(
                self.device_config["name"] +
                ": Es konnten keine Werte gelesen werden, da noch keine Komponenten konfiguriert wurden."
            )
