#!/usr/bin/env python3
import logging

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, IndependentComponentUpdater
from modules.devices.sunways.sunways.config import Sunways, SunwaysInverterSetup
from modules.devices.sunways.sunways.inverter import SunwaysInverter

log = logging.getLogger(__name__)


def create_device(device_config: Sunways):
    def create_inverter_component(component_config: SunwaysInverterSetup):
        return SunwaysInverter(component_config,
                               device_config.configuration.ip_address,
                               device_config.configuration.password)

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            inverter=create_inverter_component,
        ),
        component_updater=IndependentComponentUpdater(lambda component: component.update())
    )


device_descriptor = DeviceDescriptor(configuration_factory=Sunways)
