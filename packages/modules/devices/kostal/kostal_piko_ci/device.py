#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.kostal.kostal_piko_ci.counter import KostalPikoCiCounter
from modules.devices.kostal.kostal_piko_ci.inverter import KostalPikoCiInverter
from modules.devices.kostal.kostal_piko_ci.config import (KostalPikoCi, KostalPikoCiCounterSetup,
                                                          KostalPikoCiInverterSetup)

log = logging.getLogger(__name__)


def create_device(device_config: KostalPikoCi):
    client = None

    def create_counter_component(component_config: KostalPikoCiCounterSetup):
        nonlocal client
        return KostalPikoCiCounter(component_config, device_id=device_config.id, client=client)

    def create_inverter_component(component_config: KostalPikoCiInverterSetup):
        nonlocal client
        return KostalPikoCiInverter(component_config, device_id=device_config.id, client=client)

    def update_components(components: Iterable[Union[KostalPikoCiCounter, KostalPikoCiInverter]]):
        nonlocal client
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update()

    def initializer():
        nonlocal client
        client = ModbusTcpClient_(device_config.configuration.ip_address, device_config.configuration.port)

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=KostalPikoCi)
