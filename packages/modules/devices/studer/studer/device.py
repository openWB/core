#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.studer.studer.bat import StuderBat
from modules.devices.studer.studer.config import Studer, StuderBatSetup, StuderInverterSetup
from modules.devices.studer.studer.inverter import StuderInverter

log = logging.getLogger(__name__)


def create_device(device_config: Studer):
    client = None

    def create_bat_component(component_config: StuderBatSetup):
        nonlocal client
        return StuderBat(component_config, client=client)

    def create_inverter_component(component_config: StuderInverterSetup):
        nonlocal client
        return StuderInverter(component_config, client=client)

    def update_components(components: Iterable[Union[StuderBat, StuderInverter]]):
        nonlocal client
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update()

    def initializer():
        nonlocal client
        client = modbus.ModbusTcpClient_(device_config.configuration.ip_address, device_config.configuration.port)

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Studer)
