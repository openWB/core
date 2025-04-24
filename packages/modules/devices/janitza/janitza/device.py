#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.devices.janitza.janitza import counter, inverter, bat
from modules.devices.janitza.janitza.config import Janitza, JanitzaCounterSetup, JanitzaInverterSetup, JanitzaBatSetup

log = logging.getLogger(__name__)


def create_device(device_config: Janitza):
    client = None

    def create_counter_component(component_config: JanitzaCounterSetup):
        nonlocal client
        return counter.JanitzaCounter(component_config, device_id=device_config.id, tcp_client=client,
                                      modbus_id=device_config.configuration.modbus_id)

    def create_inverter_component(component_config: JanitzaInverterSetup):
        nonlocal client
        return inverter.JanitzaInverter(component_config, device_id=device_config.id, tcp_client=client,
                                        modbus_id=device_config.configuration.modbus_id)

    def create_bat_component(component_config: JanitzaBatSetup):
        nonlocal client
        return bat.JanitzaBat(component_config, device_id=device_config.id, tcp_client=client,
                              modbus_id=device_config.configuration.modbus_id)

    def update_components(components: Iterable[Union[counter.JanitzaCounter, inverter.JanitzaInverter,
                                                     bat.JanitzaBat]]):
        nonlocal client
        with client:
            for component in components:
                component.update()

    def initializer():
        nonlocal client
        client = modbus.ModbusTcpClient_(device_config.configuration.ip_address, device_config.configuration.port)

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


device_descriptor = DeviceDescriptor(configuration_factory=Janitza)
