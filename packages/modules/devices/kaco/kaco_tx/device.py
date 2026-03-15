#!/usr/bin/env python3
import logging
from typing import Iterable

from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.kaco.kaco_tx.inverter import KacoInverter
from modules.devices.kaco.kaco_tx.config import (Kaco, KacoInverterSetup)

log = logging.getLogger(__name__)

reconnect_delay = 1.2


def create_device(device_config: Kaco):
    client = None

    def create_inverter_component(component_config: KacoInverterSetup):
        nonlocal client
        return KacoInverter(component_config, client=client)

    def update_components(components: Iterable[KacoInverter]):
        nonlocal client
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update()

    def initializer():
        nonlocal client
        client = modbus.ModbusTcpClient_(device_config.configuration.ip_address,
                                         device_config.configuration.port,
                                         reconnect_delay=reconnect_delay)

    device = ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            inverter=create_inverter_component
        ),
        component_updater=MultiComponentUpdater(update_components)
    )
    return device


device_descriptor = DeviceDescriptor(configuration_factory=Kaco)
