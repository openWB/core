#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.anker.solarbank_4_e5000.bat import AnkerBat
from modules.devices.anker.solarbank_4_e5000.config import Anker, AnkerBatSetup, AnkerInverterSetup
from modules.devices.anker.solarbank_4_e5000.inverter import AnkerInverter

log = logging.getLogger(__name__)


def create_device(device_config: Anker):
    client = None

    def create_bat_component(component_config: AnkerBatSetup):
        return AnkerBat(component_config, device_config=device_config, client=client)

    def create_inverter_component(component_config: AnkerInverterSetup):
        return AnkerInverter(component_config, device_config=device_config, client=client)

    def update_components(components: Iterable[Union[AnkerBat, AnkerInverter]]):
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


device_descriptor = DeviceDescriptor(configuration_factory=Anker)
