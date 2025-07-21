#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.ampere.ampere.bat import AmpereBat
from modules.devices.ampere.ampere.config import Ampere, AmpereBatSetup, AmpereCounterSetup, AmpereInverterSetup
from modules.devices.ampere.ampere.counter import AmpereCounter
from modules.devices.ampere.ampere.inverter import AmpereInverter

log = logging.getLogger(__name__)


def create_device(device_config: Ampere):
    client = None

    def create_bat_component(component_config: AmpereBatSetup):
        nonlocal client
        return AmpereBat(component_config=component_config,
                         device_id=device_config.id,
                         modbus_id=device_config.configuration.modbus_id,
                         client=client)

    def create_counter_component(component_config: AmpereCounterSetup):
        nonlocal client
        return AmpereCounter(component_config=component_config,
                             device_id=device_config.id,
                             modbus_id=device_config.configuration.modbus_id,
                             client=client)

    def create_inverter_component(component_config: AmpereInverterSetup):
        nonlocal client
        return AmpereInverter(component_config=component_config,
                              device_id=device_config.id,
                              modbus_id=device_config.configuration.modbus_id,
                              client=client)

    def update_components(components: Iterable[Union[AmpereBat, AmpereCounter, AmpereInverter]]):
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


device_descriptor = DeviceDescriptor(configuration_factory=Ampere)
