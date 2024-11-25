#!/usr/bin/env python3
import logging

from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, IndependentComponentUpdater
from modules.devices.sma.sma_webbox.config import SmaWebbox, SmaWebboxInverterSetup
from modules.common.abstract_device import DeviceDescriptor
from modules.devices.sma.sma_webbox.inverter import SmaWebboxInverter


log = logging.getLogger(__name__)


def create_device(device_config: SmaWebbox):
    def create_inverter_component(component_config: SmaWebboxInverterSetup):
        return SmaWebboxInverter(device_config.configuration.ip_address, component_config)

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            inverter=create_inverter_component,
        ),
        component_updater=IndependentComponentUpdater(lambda component: component.update())
    )


device_descriptor = DeviceDescriptor(configuration_factory=SmaWebbox)
