#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.fronius.fronius_sunspec.bat import FroniusSunspecBat
from modules.devices.fronius.fronius_sunspec.config import (
    FroniusSunspec, FroniusSunspecBatSetup, FroniusSunspecCounterSetup, FroniusSunspecInverterSetup)
from modules.devices.fronius.fronius_sunspec.counter import FroniusSunspecCounter
from modules.devices.fronius.fronius_sunspec.inverter import FroniusSunspecInverter

log = logging.getLogger(__name__)


fronius_sunspec_component_classes = Union[FroniusSunspecBat, FroniusSunspecCounter, FroniusSunspecInverter]


def create_device(device_config: FroniusSunspec):
    client = None

    def create_bat_component(component_config: FroniusSunspecBatSetup):
        return FroniusSunspecBat(component_config, device_id=device_config.id, client=client)

    def create_counter_component(component_config: FroniusSunspecCounterSetup):
        return FroniusSunspecCounter(component_config, device_id=device_config.id, client=client,
                                     device_config=device_config.configuration)

    def create_inverter_component(component_config: FroniusSunspecInverterSetup):
        return FroniusSunspecInverter(component_config, device_id=device_config.id, client=client)

    def update_components(components: Iterable[fronius_sunspec_component_classes]):
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


device_descriptor = DeviceDescriptor(configuration_factory=FroniusSunspec)
