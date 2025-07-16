#!/usr/bin/env python3
import logging
from typing import Iterable

from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.algodue.algodue import counter
from modules.devices.algodue.algodue.config import Algodue, AlgodueCounterSetup
from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext

log = logging.getLogger(__name__)


def create_device(device_config: Algodue):
    client = None

    def create_counter_component(component_config: AlgodueCounterSetup):
        nonlocal client
        return counter.AlgodueCounter(component_config=component_config, device_id=device_config.id,
                                      tcp_client=client, modbus_id=device_config.configuration.modbus_id)

    def update_components(components: Iterable[counter.AlgodueCounter]):
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state, update_always=False):
                    component.update()

    def initializer():
        nonlocal client
        client = modbus.ModbusTcpClient_(device_config.configuration.ip_address, device_config.configuration.port)

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            counter=create_counter_component
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Algodue)
