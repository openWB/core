#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.siemens.siemens_logo84.config import (SiemensLogo84, SiemensLogo84BatSetup)
from modules.devices.siemens.siemens_logo84 import bat

log = logging.getLogger(__name__)


def create_device(device_config: SiemensLogo84):
    client = None

    def create_bat_component(component_config: SiemensLogo84BatSetup):
        nonlocal client
        return bat.SiemensLogo84Bat(component_config, client=client, modbus_id=device_config.configuration.modbus_id)

    def update_components(components: Iterable[Union[bat.SiemensLogo84Bat]]):
        nonlocal client
        with client:
            for component in components:
                component.update()

    def initializer():
        nonlocal client
        client = ModbusTcpClient_(device_config.configuration.ip_address, device_config.configuration.port)

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=SiemensLogo84)
