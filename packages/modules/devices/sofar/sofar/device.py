#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.sofar.sofar.bat import SofarBat
from modules.devices.sofar.sofar.config import Sofar, SofarBatSetup, SofarCounterSetup, SofarInverterSetup
from modules.devices.sofar.sofar.counter import SofarCounter
from modules.devices.sofar.sofar.inverter import SofarInverter

log = logging.getLogger(__name__)


def create_device(device_config: Sofar):
    client = None

    def create_bat_component(component_config: SofarBatSetup):
        nonlocal client
        return SofarBat(component_config, device_config.configuration.modbus_id, client)

    def create_counter_component(component_config: SofarCounterSetup):
        nonlocal client
        return SofarCounter(component_config, device_config.configuration.modbus_id, client)

    def create_inverter_component(component_config: SofarInverterSetup):
        nonlocal client
        return SofarInverter(component_config, device_config.configuration.modbus_id, client)

    def update_components(components: Iterable[Union[SofarBat, SofarCounter, SofarInverter]]):
        nonlocal client
        with client as c:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update(c)

    def initialiser():
        nonlocal client
        client = ModbusTcpClient_(device_config.configuration.ip_address, device_config.configuration.port)

    return ConfigurableDevice(
        device_config=device_config,
        initialiser=initialiser,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Sofar)
