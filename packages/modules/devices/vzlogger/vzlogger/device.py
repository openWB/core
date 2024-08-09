#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.devices.vzlogger.vzlogger.config import VZLogger, VZLoggerCounterSetup, VZLoggerInverterSetup
from modules.devices.vzlogger.vzlogger.counter import VZLoggerCounter
from modules.devices.vzlogger.vzlogger.inverter import VZLoggerInverter

log = logging.getLogger(__name__)


def create_device(device_config: VZLogger):
    def create_counter_component(component_config: VZLoggerCounterSetup):
        return VZLoggerCounter(device_config.id, component_config)

    def create_inverter_component(component_config: VZLoggerInverterSetup):
        return VZLoggerInverter(device_config.id, component_config)

    def update_components(components: Iterable[Union[VZLoggerCounter, VZLoggerInverter]]):
        response = req.get_http_session().get(device_config.configuration.ip_address, timeout=5).json()
        for component in components:
            component.update(response)

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=VZLogger)
