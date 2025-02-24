#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.solax.solax.bat import SolaxBat
from modules.devices.solax.solax.config import Solax, SolaxBatSetup, SolaxCounterSetup, SolaxInverterSetup
from modules.devices.solax.solax.counter import SolaxCounter
from modules.devices.solax.solax.inverter import SolaxInverter

log = logging.getLogger(__name__)


def create_device(device_config: Solax):
    client = None

    def create_bat_component(component_config: SolaxBatSetup):
        return SolaxBat(component_config, device_config=device_config, client=client)

    def create_counter_component(component_config: SolaxCounterSetup):
        return SolaxCounter(component_config, device_config=device_config, client=client)

    def create_inverter_component(component_config: SolaxInverterSetup):
        return SolaxInverter(component_config, device_config=device_config, client=client)

    def update_components(components: Iterable[Union[SolaxBat, SolaxCounter, SolaxInverter]]):
        nonlocal client
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


device_descriptor = DeviceDescriptor(configuration_factory=Solax)
