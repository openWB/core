#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common.modbus import ModbusUdpClient_
from modules.devices.victron.victron_3p75ct.config import Victron, VictronCounterSetup
from modules.devices.victron.victron_3p75ct.counter import VictronCounter

log = logging.getLogger(__name__)


def create_device(device_config: Victron):
    client = None

    def create_counter_component(component_config: VictronCounterSetup):
        nonlocal client
        return VictronCounter(component_config, device_id=device_config.id, client=client)


    def update_components(components: Iterable[VictronCounter]):
        nonlocal client
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update()

    def initializer():
        nonlocal client
        client = ModbusUdpClient_(device_config.configuration.ip_address, device_config.configuration.port, timeout=30)

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            counter=create_counter_component
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Victron)
