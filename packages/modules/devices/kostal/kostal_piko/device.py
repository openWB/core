#!/usr/bin/env python3
import logging

from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, IndependentComponentUpdater
from modules.common.abstract_device import DeviceDescriptor
from modules.devices.kostal.kostal_piko import counter
from modules.devices.kostal.kostal_piko import inverter
from modules.devices.kostal.kostal_piko.config import KostalPiko, KostalPikoCounterSetup, KostalPikoInverterSetup

log = logging.getLogger(__name__)


def create_device(device_config: KostalPiko):
    def create_counter_component(component_config: KostalPikoCounterSetup):
        return counter.KostalPikoCounter(device_config.id, component_config, device_config.configuration.ip_address)

    def create_inverter_component(component_config: KostalPikoInverterSetup):
        return inverter.KostalPikoInverter(device_config.id, component_config, device_config.configuration.ip_address)

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=IndependentComponentUpdater(lambda component: component.update())
    )


device_descriptor = DeviceDescriptor(configuration_factory=KostalPiko)
