#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.solar_view.solar_view.counter import SolarViewCounter
from modules.devices.solar_view.solar_view.config import SolarView, SolarViewCounterSetup, SolarViewInverterSetup
from modules.devices.solar_view.solar_view.inverter import SolarViewInverter
log = logging.getLogger(__name__)


def create_device(device_config: SolarView):
    def create_counter_component(component_config: SolarViewCounterSetup):
        return SolarViewCounter(component_config)

    def create_inverter_component(component_config: SolarViewInverterSetup):
        return SolarViewInverter(component_config)

    def update_components(components: Iterable[Union[SolarViewCounter, SolarViewInverter]]):
        # Fehler pro Komponente isoliert, statt bei einem Fehler alle als defekt zu markieren.
        for component in components:
            with SingleComponentUpdateContext(component.fault_state):
                component.update(
                    device_config.configuration.ip_address,
                    device_config.configuration.port,
                    device_config.configuration.timeout)

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=SolarView)
