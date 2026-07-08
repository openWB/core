#!/usr/bin/env python3
import logging

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, IndependentComponentUpdater
from modules.common.req import get_http_session
from modules.devices.powerfox.powerfox.counter import PowerfoxCounter
from modules.devices.powerfox.powerfox.config import Powerfox, PowerfoxCounterSetup, PowerfoxInverterSetup
from modules.devices.powerfox.powerfox.inverter import PowerfoxInverter
log = logging.getLogger(__name__)


def create_device(device_config: Powerfox):
    session = None

    def create_counter_component(component_config: PowerfoxCounterSetup):
        return PowerfoxCounter(component_config)

    def create_inverter_component(component_config: PowerfoxInverterSetup):
        return PowerfoxInverter(component_config)

    def initializer():
        nonlocal session
        session = get_http_session()
        session.auth = (device_config.configuration.user, device_config.configuration.password)

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=IndependentComponentUpdater(lambda component: component.update(session))
    )


device_descriptor = DeviceDescriptor(configuration_factory=Powerfox)
