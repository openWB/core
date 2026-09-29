#!/usr/bin/env python3
import logging

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, IndependentComponentUpdater
from modules.devices.solar_view.solar_view.counter import SolarViewCounter
from modules.devices.solar_view.solar_view.config import SolarView, SolarViewCounterSetup, SolarViewInverterSetup
from modules.devices.solar_view.solar_view.inverter import SolarViewInverter
log = logging.getLogger(__name__)


def create_device(device_config: SolarView):
    def create_counter_component(component_config: SolarViewCounterSetup):
        return SolarViewCounter(component_config)

    def create_inverter_component(component_config: SolarViewInverterSetup):
        return SolarViewInverter(component_config)

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=IndependentComponentUpdater(lambda component: component.update(
            device_config.configuration.ip_address,
            device_config.configuration.port,
            device_config.configuration.timeout))
    )


device_descriptor = DeviceDescriptor(configuration_factory=SolarView)
