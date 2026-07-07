#!/usr/bin/env python3
import logging
from typing import Iterable,  Union

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.devices.solar_world.solar_world.config import (
    SolarWorld, SolarWorldCounterSetup, SolarWorldInverterSetup)
from modules.devices.solar_world.solar_world.counter import SolarWorldCounter
from modules.devices.solar_world.solar_world.inverter import SolarWorldInverter

log = logging.getLogger(__name__)


def create_device(device_config: SolarWorld):
    def create_counter_component(component_config: SolarWorldCounterSetup):
        return SolarWorldCounter(component_config, device_id=device_config.id)

    def create_inverter_component(component_config: SolarWorldInverterSetup):
        return SolarWorldInverter(component_config, device_id=device_config.id)

    def update_components(components: Iterable[Union[SolarWorldCounter, SolarWorldInverter]]):
        response = req.get_http_session().get("http://"+str(device_config.configuration.ip_address) +
                                              "/rest/solarworld/lpvm/powerAndBatteryData", timeout=5).json()
        for component in components:
            with SingleComponentUpdateContext(component.fault_state):
                component.update(response)

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=SolarWorld)
