#!/usr/bin/env python3
from typing import Dict, Union
import logging

from dataclass_utils import dataclass_from_dict
from modules.common.abstract_device import AbstractDevice, DeviceDescriptor
from modules.common.component_context import MultiComponentUpdateContext
from modules.mqtt import bat, counter, inverter
from modules.mqtt.config import Mqtt, MqttBatSetup, MqttCounterSetup, MqttInverterSetup

log = logging.getLogger(__name__)


class Device(AbstractDevice):
    COMPONENT_TYPE_TO_CLASS = {
        "bat": bat.MqttBat,
        "counter": counter.MqttCounter,
        "inverter": inverter.MqttInverter
    }
    COMPONENT_TYPE_TO_MODULE = {
        "bat": bat,
        "counter": counter,
        "inverter": inverter
    }

    def __init__(self, device_config: Union[Dict, Mqtt]) -> None:
        self.components = {}
        try:
            self.device_config = dataclass_from_dict(Mqtt, device_config)
        except Exception:
            log.exception("Fehler im Modul " + self.device_config.name)

    def add_component(self, component_config: Union[Dict, MqttBatSetup, MqttCounterSetup, MqttInverterSetup]) -> None:
        if isinstance(component_config, Dict):
            component_type = component_config["type"]
        else:
            component_type = component_config.type
        component_config = dataclass_from_dict(self.COMPONENT_TYPE_TO_MODULE[
            component_type].component_descriptor.configuration_factory, component_config)
        if component_type in self.COMPONENT_TYPE_TO_CLASS:
            self.components["component"+str(component_config.id)
                            ] = (self.COMPONENT_TYPE_TO_CLASS[component_type](component_config))

    def update(self) -> None:
        if self.components:
            with MultiComponentUpdateContext(self.components):
                log.debug("MQTT-Module müssen nicht ausgelesen werden.")
        else:
            log.warning(
                self.device_config.name +
                ": Es konnten keine Werte gelesen werden, da noch keine Komponenten konfiguriert wurden."
            )


device_descriptor = DeviceDescriptor(configuration_factory=Mqtt)
