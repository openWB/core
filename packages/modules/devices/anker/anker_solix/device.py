#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.anker.anker_solix.bat import AnkerBat
from modules.devices.anker.anker_solix.config import Anker, AnkerBatSetup, AnkerCounterSetup, AnkerInverterSetup
from modules.devices.anker.anker_solix.counter import AnkerCounter
from modules.devices.anker.anker_solix.inverter import AnkerInverter

log = logging.getLogger(__name__)


def create_device(device_config: Anker):
    client = None

    def create_bat_component(component_config: AnkerBatSetup):
        nonlocal client
        return AnkerBat(component_config, device_id=device_config.id, client=client)

    def create_counter_component(component_config: AnkerCounterSetup):
        nonlocal client
        return AnkerCounter(component_config, device_id=device_config.id, client=client)

    def create_inverter_component(component_config: AnkerInverterSetup):
        nonlocal client
        return AnkerInverter(component_config, device_id=device_config.id, client=client)

    def update_components(components: Iterable[Union[AnkerBat, AnkerCounter, AnkerInverter]]):
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


device_descriptor = DeviceDescriptor(configuration_factory=Anker)
