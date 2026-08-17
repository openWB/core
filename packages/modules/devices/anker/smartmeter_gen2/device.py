#!/usr/bin/env python3
import logging
from typing import Iterable

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.anker.smartmeter_gen2.config import AnkerMeter, AnkerMeterCounterSetup
from modules.devices.anker.smartmeter_gen2.counter import AnkerMeterCounter

log = logging.getLogger(__name__)


def create_device(device_config: AnkerMeter):
    client = None

    def create_counter_component(component_config: AnkerMeterCounterSetup):
        return AnkerMeterCounter(component_config, device_config=device_config, client=client)

    def update_components(components: Iterable[AnkerMeterCounter]):
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
        component_factory=ComponentFactoryByType(counter=create_counter_component),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=AnkerMeter)
