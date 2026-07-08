#!/usr/bin/env python3
import logging
from typing import Iterable

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.devices.youless.youless.config import Youless, YoulessInverterSetup
from modules.devices.youless.youless.inverter import YoulessInverter

log = logging.getLogger(__name__)


def create_device(device_config: Youless):
    def create_inverter_component(component_config: YoulessInverterSetup):
        return YoulessInverter(component_config)

    def update_components(components: Iterable[YoulessInverter]):
        response = req.get_http_session().get("http://"+device_config.configuration.ip_address+'/a',
                                              params=(('f', 'j'),),
                                              timeout=5).json()
        for component in components:
            with SingleComponentUpdateContext(component.fault_state):
                component.update(response)

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Youless)
