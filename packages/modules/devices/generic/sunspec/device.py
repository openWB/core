#!/usr/bin/env python3
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.generic.sunspec.bat import SunspecBat
from modules.devices.generic.sunspec.config import Sunspec, SunspecBatSetup, SunspecCounterSetup, SunspecInverterSetup
from modules.devices.generic.sunspec.counter import SunspecCounter
from modules.devices.generic.sunspec.inverter import SunspecInverter

sunspec_component_classes = Union[SunspecBat, SunspecCounter, SunspecInverter]


def create_device(device_config: Sunspec):
    client = None

    def create_bat_component(component_config: SunspecBatSetup):
        return SunspecBat(component_config, device_id=device_config.id, client=client)

    def create_counter_component(component_config: SunspecCounterSetup):
        return SunspecCounter(component_config, device_id=device_config.id, client=client)

    def create_inverter_component(component_config: SunspecInverterSetup):
        return SunspecInverter(component_config, device_id=device_config.id, client=client)

    def update_components(components: Iterable[sunspec_component_classes]):
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


device_descriptor = DeviceDescriptor(configuration_factory=Sunspec)
