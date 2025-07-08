#!/usr/bin/env python3
import logging
from pathlib import Path
from typing import Iterable, Union

from helpermodules.utils.run_command import run_command
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.growatt.growatt.bat import GrowattBat
from modules.devices.growatt.growatt.config import Growatt, GrowattBatSetup, GrowattCounterSetup, GrowattInverterSetup
from modules.devices.growatt.growatt.counter import GrowattCounter
from modules.devices.growatt.growatt.inverter import GrowattInverter
from modules.devices.growatt.growatt.version import GrowattVersion

log = logging.getLogger(__name__)


def create_device(device_config: Growatt):
    client = None

    def create_bat_component(component_config: GrowattBatSetup):
        nonlocal client
        return GrowattBat(component_config=component_config,
                          modbus_id=device_config.configuration.modbus_id,
                          version=GrowattVersion(device_config.configuration.version),
                          client=client)

    def create_counter_component(component_config: GrowattCounterSetup):
        nonlocal client
        return GrowattCounter(component_config=component_config,
                              modbus_id=device_config.configuration.modbus_id,
                              version=GrowattVersion(device_config.configuration.version),
                              client=client)

    def create_inverter_component(component_config: GrowattInverterSetup):
        nonlocal client
        return GrowattInverter(component_config=component_config,
                               modbus_id=device_config.configuration.modbus_id,
                               version=GrowattVersion(device_config.configuration.version),
                               client=client)

    def update_components(components: Iterable[Union[GrowattBat, GrowattCounter, GrowattInverter]]):
        nonlocal client
        with client:
            for component in components:
                component.update()

    def initializer():
        nonlocal client
        client = ModbusTcpClient_(device_config.configuration.ip_address, device_config.configuration.port)

    def error_handler():
        run_command(f"{Path(__file__).resolve().parents[4]}/modules/common/restart_protoss_admin")

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        error_handler=error_handler,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Growatt)
