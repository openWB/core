#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.solis.solis.bat import SolisBat
from modules.devices.solis.solis.counter import SolisCounter
from modules.devices.solis.solis.inverter import SolisInverter
from modules.devices.solis.solis.config import Solis, SolisBatSetup, SolisCounterSetup, SolisInverterSetup
from modules.devices.solis.solis.version import SolisVersion

log = logging.getLogger(__name__)


def create_device(device_config: Solis):
    client = None

    def create_bat_component(component_config: SolisBatSetup):
        nonlocal client
        return SolisBat(component_config, client=client)

    def create_counter_component(component_config: SolisCounterSetup):
        nonlocal client
        return SolisCounter(component_config, version=SolisVersion(device_config.configuration.version), client=client)

    def create_inverter_component(component_config: SolisInverterSetup):
        nonlocal client
        return SolisInverter(component_config,
                             version=SolisVersion(device_config.configuration.version),
                             client=client)

    def update_components(components: Iterable[Union[SolisBat, SolisCounter, SolisInverter]]):
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


device_descriptor = DeviceDescriptor(configuration_factory=Solis)
