#!/usr/bin/env python3
import logging
from typing import Iterable

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.devices.kostal.kostal_piko_old.config import (KostalPikoOld,
                                                           KostalPikoOldInverterSetup)
from modules.devices.kostal.kostal_piko_old.inverter import KostalPikoOldInverter

log = logging.getLogger(__name__)


def create_device(device_config: KostalPikoOld):
    def create_inverter_component(component_config: KostalPikoOldInverterSetup):
        return KostalPikoOldInverter(component_config, device_id=device_config.id)

    def update_components(components: Iterable[KostalPikoOldInverter]):
        response = req.get_http_session().get(device_config.configuration.url, verify=False, auth=(
            device_config.configuration.user, device_config.configuration.password), timeout=5).text
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


device_descriptor = DeviceDescriptor(configuration_factory=KostalPikoOld)
