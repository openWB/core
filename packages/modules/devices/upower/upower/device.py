#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.upower.upower.bat import UPowerBat
from modules.devices.upower.upower.config import UPower, UPowerBatSetup, UPowerCounterSetup, UPowerInverterSetup
from modules.devices.upower.upower.counter import UPowerCounter
from modules.devices.upower.upower.inverter import UPowerInverter
from modules.devices.upower.upower.version import UPowerVersion

log = logging.getLogger(__name__)


def create_device(device_config: UPower):
    client = None

    def create_bat_component(component_config: UPowerBatSetup):
        nonlocal client
        return UPowerBat(component_config,
                         UPowerVersion(device_config.configuration.version),
                         device_config.configuration.modbus_id, client, device_config.id)

    def create_counter_component(component_config: UPowerCounterSetup):
        nonlocal client
        return UPowerCounter(component_config,
                             UPowerVersion(device_config.configuration.version),
                             device_config.configuration.modbus_id, client, device_config.id)

    def create_inverter_component(component_config: UPowerInverterSetup):
        nonlocal client
        return UPowerInverter(component_config,
                              UPowerVersion(device_config.configuration.version),
                              device_config.configuration.modbus_id, client)

    def update_components(components: Iterable[Union[UPowerBat, UPowerCounter, UPowerInverter]]):
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
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=UPower)
