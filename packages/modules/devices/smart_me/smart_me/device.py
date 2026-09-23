#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common.req import get_http_session
from modules.devices.smart_me.smart_me.counter import SmartMeCounter
from modules.devices.smart_me.smart_me.config import SmartMe, SmartMeCounterSetup, SmartMeInverterSetup
from modules.devices.smart_me.smart_me.inverter import SmartMeInverter

log = logging.getLogger(__name__)


def create_device(device_config: SmartMe):
    session = None

    def create_counter_component(component_config: SmartMeCounterSetup):
        return SmartMeCounter(component_config)

    def create_inverter_component(component_config: SmartMeInverterSetup):
        return SmartMeInverter(component_config)

    def initializer():
        nonlocal session
        session = get_http_session()
        session.auth = (device_config.configuration.user, device_config.configuration.password)

    def update_components(components: Iterable[Union[SmartMeCounter, SmartMeInverter]]):
        # Fehler pro Komponente isoliert, statt bei einem Fehler alle als defekt zu markieren.
        for component in components:
            with SingleComponentUpdateContext(component.fault_state):
                component.update(session)

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=SmartMe)
