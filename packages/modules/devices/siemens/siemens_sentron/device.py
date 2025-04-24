#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.siemens.siemens_sentron.config import (SiemensSentron, SiemensSentronCounterSetup,
                                                            SiemensSentronInverterSetup, SiemensSentronBatSetup)
from modules.devices.siemens.siemens_sentron import counter, inverter, bat

log = logging.getLogger(__name__)


def create_device(device_config: SiemensSentron):
    client = None

    def create_counter_component(component_config: SiemensSentronCounterSetup):
        nonlocal client
        return counter.SiemensSentronCounter(component_config, client=client,
                                             modbus_id=device_config.configuration.modbus_id)

    def create_inverter_component(component_config: SiemensSentronInverterSetup):
        nonlocal client
        return inverter.SiemensSentronInverter(component_config, client=client,
                                               modbus_id=device_config.configuration.modbus_id)

    def create_bat_component(component_config: SiemensSentronBatSetup):
        nonlocal client
        return bat.SiemensSentronBat(component_config, client=client,
                                     modbus_id=device_config.configuration.modbus_id)

    def update_components(components: Iterable[Union[counter.SiemensSentronCounter, inverter.SiemensSentronInverter,
                                                     bat.SiemensSentronBat]]):
        nonlocal client
        with client:
            for component in components:
                component.update()

    def initializer():
        nonlocal client
        client = ModbusTcpClient_(device_config.configuration.ip_address, device_config.configuration.port)

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            counter=create_counter_component,
            inverter=create_inverter_component,
            bat=create_bat_component
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=SiemensSentron)
