#!/usr/bin/env python3
from typing import Iterable, Union
import logging

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.generic.mqtt import bat, counter, inverter
from modules.devices.generic.mqtt.config import Mqtt, MqttBatSetup, MqttCounterSetup, MqttInverterSetup

log = logging.getLogger(__name__)


def create_device(device_config: Mqtt):
    def create_bat_component(component_config: MqttBatSetup):
        return bat.MqttBat(component_config)

    def create_counter_component(component_config: MqttCounterSetup):
        return counter.MqttCounter(component_config)

    def create_inverter_component(component_config: MqttInverterSetup):
        return inverter.MqttInverter(component_config)

    def update_components(components: Iterable[Union[bat.MqttBat, counter.MqttCounter, inverter.MqttInverter]]):
        log.debug("MQTT-Module müssen nicht ausgelesen werden.")

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Mqtt)
