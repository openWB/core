#!/usr/bin/env python3
import logging
from typing import Iterable

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.idm.idm.config import IDM, IDMCounterSetup
from modules.devices.idm.idm.counter import IDMCounter

log = logging.getLogger(__name__)


def create_device(device_config: IDM):
    client = None

    def create_counter_component(component_config: IDMCounterSetup):
        nonlocal client
        return IDMCounter(component_config,
                          device_id=device_config.id,
                          client=client,
                          modbus_id=device_config.configuration.modbus_id)

    def update_components(components: Iterable[IDMCounter]):
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
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=IDM)
