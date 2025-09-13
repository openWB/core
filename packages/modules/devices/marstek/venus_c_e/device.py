#!/usr/bin/env python3
import logging
from typing import Iterable,  Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.marstek.venus_c_e.bat import VenusCEBat
from modules.devices.marstek.venus_c_e.config import VenusCE, VenusCEBatSetup

log = logging.getLogger(__name__)


def create_device(device_config: VenusCE):
    client = None

    def create_bat_component(component_config: VenusCEBatSetup):
        nonlocal client
        return VenusCEBat(component_config, device_id=device_config.id, client=client)

    def update_components(components: Iterable[VenusCEBat]):
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
            bat=create_bat_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=VenusCE)
