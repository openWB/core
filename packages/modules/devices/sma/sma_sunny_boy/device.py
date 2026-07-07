#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.sma.sma_sunny_boy.bat import SunnyBoyBat
from modules.devices.sma.sma_sunny_boy.config import (SmaSunnyBoy, SmaSunnyBoyBatSetup, SmaSunnyBoyCounterSetup,
                                                      SmaSunnyBoyInverterSetup)
from modules.devices.sma.sma_sunny_boy.counter import SmaSunnyBoyCounter
from modules.devices.sma.sma_sunny_boy.inverter import SmaSunnyBoyInverter

log = logging.getLogger(__name__)


sma_modbus_tcp_component_classes = Union[
    SunnyBoyBat,
    SmaSunnyBoyCounter,
    SmaSunnyBoyInverter
]


def create_device(device_config: SmaSunnyBoy):
    client = None

    def create_bat_component(component_config: SmaSunnyBoyBatSetup):
        return SunnyBoyBat(component_config, device_id=device_config.id, client=client)

    def create_counter_component(component_config: SmaSunnyBoyCounterSetup):
        return SmaSunnyBoyCounter(component_config, device_id=device_config.id, client=client)

    def create_inverter_component(component_config: SmaSunnyBoyInverterSetup):
        return SmaSunnyBoyInverter(component_config, client=client, device_id=device_config.id)

    def update_components(components: Iterable[sma_modbus_tcp_component_classes]):
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


device_descriptor = DeviceDescriptor(configuration_factory=SmaSunnyBoy)
