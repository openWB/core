#!/usr/bin/env python3
import logging

from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, IndependentComponentUpdater
from modules.devices.byd.byd.config import BYD, BYDBatSetup
from modules.devices.byd.byd import bat
from modules.common.abstract_device import DeviceDescriptor

log = logging.getLogger(__name__)


def create_device(device_config: BYD):
    def create_bat_component(component_config: BYDBatSetup):
        return bat.BYDBat(component_config, device_config)

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component
        ),
        component_updater=IndependentComponentUpdater(lambda component: component.update())
    )


device_descriptor = DeviceDescriptor(configuration_factory=BYD)
