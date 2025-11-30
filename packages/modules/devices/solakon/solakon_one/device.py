#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.solakon.solakon_one.bat import SolakonOneBat
from modules.devices.solakon.solakon_one.inverter import SolakonOneInverter
from modules.devices.solakon.solakon_one.config import SolakonOne, SolakonOneBatSetup, SolakonOneInverterSetup

log = logging.getLogger(__name__)


def create_device(device_config: SolakonOne):
    client = None

    def create_bat_component(component_config: SolakonOneBatSetup):
        nonlocal client
        return SolakonOneBat(component_config=component_config, client=client)

    def create_inverter_component(component_config: SolakonOneInverterSetup):
        nonlocal client
        return SolakonOneInverter(component_config=component_config, client=client)

    def update_components(components: Iterable[Union[SolakonOneBat, SolakonOneInverter]]):
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
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=SolakonOne)
