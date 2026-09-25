#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.devices.generic.http.bat import HttpBat
from modules.devices.generic.http.config import (HTTP, HttpBatSetup, HttpCounterSetup,
                                                 HttpInverterSetup)
from modules.devices.generic.http.counter import HttpCounter
from modules.devices.generic.http.inverter import HttpInverter

log = logging.getLogger(__name__)


def create_device(device_config: HTTP):
    session = None

    def create_bat_component(component_config: HttpBatSetup):
        return HttpBat(component_config=component_config,
                       device_id=device_config.id,
                       url=device_config.configuration.url)

    def create_counter_component(component_config: HttpCounterSetup):
        return HttpCounter(component_config=component_config,
                           device_id=device_config.id,
                           url=device_config.configuration.url)

    def create_inverter_component(component_config: HttpInverterSetup):
        return HttpInverter(component_config=component_config,
                            device_id=device_config.id,
                            url=device_config.configuration.url)

    def initializer():
        nonlocal session
        session = req.get_http_session()

    def update_components(components: Iterable[Union[HttpBat, HttpCounter, HttpInverter]]):
        # Fehler pro Komponente isoliert, statt bei einem Fehler alle als defekt zu markieren.
        for component in components:
            with SingleComponentUpdateContext(component.fault_state):
                component.update(session)

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=HTTP)
