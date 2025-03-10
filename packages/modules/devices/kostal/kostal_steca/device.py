#!/usr/bin/env python3

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, IndependentComponentUpdater
from modules.devices.kostal.kostal_steca.config import KostalSteca, KostalStecaInverterSetup
from modules.devices.kostal.kostal_steca.inverter import KostalStecaInverter


def create_device(device_config: KostalSteca):
    def create_inverter_component(component_config: KostalStecaInverterSetup):
        return KostalStecaInverter(component_config, ip_address=device_config.configuration.ip_address)

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            inverter=create_inverter_component,
        ),
        component_updater=IndependentComponentUpdater(lambda component: component.update())
    )


device_descriptor = DeviceDescriptor(configuration_factory=KostalSteca)
