#!/usr/bin/env python3
import logging
from pymodbus.transaction import ModbusRtuFramer
from typing import Iterable

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.orno.orno.config import Orno, OrnoCounterSetup
from modules.devices.orno.orno.counter import OrnoCounter

log = logging.getLogger(__name__)


def create_device(device_config: Orno):
    client = None

    def create_counter_component(component_config: OrnoCounterSetup):
        nonlocal client
        return OrnoCounter(component_config, client=client)

    def update_components(components: Iterable[OrnoCounter]):
        with client:
            for component in components:
                component.update()

    def initializer():
        nonlocal client
        client = ModbusTcpClient_(device_config.configuration.ip_address,
                                  device_config.configuration.port, framer=ModbusRtuFramer)

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            counter=create_counter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Orno)
