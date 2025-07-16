#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.victron.victron.bat import VictronBat
from modules.devices.victron.victron.config import Victron, VictronBatSetup, VictronCounterSetup, VictronInverterSetup
from modules.devices.victron.victron.counter import VictronCounter
from modules.devices.victron.victron.inverter import VictronInverter

log = logging.getLogger(__name__)


def create_device(device_config: Victron):
    client = None

    def create_bat_component(component_config: VictronBatSetup):
        nonlocal client
        return VictronBat(component_config, device_id=device_config.id, client=client)

    def create_counter_component(component_config: VictronCounterSetup):
        nonlocal client
        return VictronCounter(component_config, device_id=device_config.id, client=client)

    def create_inverter_component(component_config: VictronInverterSetup):
        nonlocal client
        return VictronInverter(component_config, device_id=device_config.id, client=client)

    def update_components(components: Iterable[Union[VictronBat, VictronCounter, VictronInverter]]):
        nonlocal client
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state, update_always=False):
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


device_descriptor = DeviceDescriptor(configuration_factory=Victron)
