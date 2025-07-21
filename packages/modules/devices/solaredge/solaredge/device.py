#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.solaredge.solaredge.bat import SolaredgeBat
from modules.devices.solaredge.solaredge.counter import SolaredgeCounter
from modules.devices.solaredge.solaredge.external_inverter import SolaredgeExternalInverter
from modules.devices.solaredge.solaredge.inverter import SolaredgeInverter
from modules.devices.solaredge.solaredge.config import (Solaredge, SolaredgeBatSetup, SolaredgeCounterSetup,
                                                        SolaredgeExternalInverterSetup, SolaredgeInverterSetup)

log = logging.getLogger(__name__)


reconnect_delay = 1.2


def create_device(device_config: Solaredge):
    client = None

    def create_bat_component(component_config: SolaredgeBatSetup):
        nonlocal client
        return SolaredgeBat(component_config, device_id=device_config.id, client=client)

    def create_counter_component(component_config: SolaredgeCounterSetup):
        nonlocal client, device
        return SolaredgeCounter(component_config, client=client, components=device.components)

    def create_inverter_component(component_config: SolaredgeInverterSetup):
        nonlocal client
        return SolaredgeInverter(component_config, client=client, device_id=device_config.id)

    def create_external_inverter_component(component_config: SolaredgeExternalInverterSetup):
        nonlocal client, device
        return SolaredgeExternalInverter(component_config, client=client, components=device.components)

    def update_components(components: Iterable[Union[SolaredgeBat, SolaredgeCounter, SolaredgeInverter]]):
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
            bat=create_bat_component,
            counter=create_counter_component,
            external_inverter=create_external_inverter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )
    return device


device_descriptor = DeviceDescriptor(configuration_factory=Solaredge)
