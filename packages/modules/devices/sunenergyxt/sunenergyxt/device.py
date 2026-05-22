#!/usr/bin/env python3
import logging
from typing import Iterable
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.sunenergyxt.sunenergyxt.bat import SunEnergyXTBat
from modules.devices.sunenergyxt.sunenergyxt.config import SunEnergyXT, SunEnergyXTBatSetup

log = logging.getLogger(__name__)


def create_device(device_config: SunEnergyXT):
    def create_bat_component(component_config: SunEnergyXTBatSetup):
        return SunEnergyXTBat(component_config, device_config=device_config)

    def update_components(components: Iterable[SunEnergyXTBat]):
        for component in components:
            with SingleComponentUpdateContext(component.fault_state):
                component.update()

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=SunEnergyXT)
