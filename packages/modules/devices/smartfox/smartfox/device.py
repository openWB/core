#!/usr/bin/env python3
import logging

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, IndependentComponentUpdater
from modules.devices.smartfox.smartfox.counter import SmartfoxCounter
from modules.devices.smartfox.smartfox.config import Smartfox, SmartfoxCounterSetup
log = logging.getLogger(__name__)


def create_device(device_config: Smartfox):
    def create_counter_component(component_config: SmartfoxCounterSetup):
        return SmartfoxCounter(component_config, ip_address=device_config.configuration.ip_address)

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            counter=create_counter_component,
        ),
        component_updater=IndependentComponentUpdater(lambda component: component.update())
    )


device_descriptor = DeviceDescriptor(configuration_factory=Smartfox)
