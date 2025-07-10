#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.good_we.good_we import bat
from modules.devices.good_we.good_we import counter
from modules.devices.good_we.good_we import inverter
from modules.devices.good_we.good_we.config import GoodWe, GoodWeBatSetup, GoodWeCounterSetup, GoodWeInverterSetup
from modules.devices.good_we.good_we.version import GoodWeVersion

log = logging.getLogger(__name__)

good_we_component_classes = Union[bat.GoodWeBat, counter.GoodWeCounter, inverter.GoodWeInverter]


def create_device(device_config: GoodWe):
    client = None

    def create_bat_component(component_config: GoodWeBatSetup):
        nonlocal client
        return bat.GoodWeBat(component_config=component_config,
                             device_id=device_config.id,
                             modbus_id=device_config.configuration.modbus_id,
                             version=GoodWeVersion(device_config.configuration.version),
                             firmware=device_config.configuration.firmware,
                             client=client)

    def create_counter_component(component_config: GoodWeCounterSetup):
        nonlocal client
        return counter.GoodWeCounter(component_config=component_config,
                                     modbus_id=device_config.configuration.modbus_id,
                                     version=GoodWeVersion(device_config.configuration.version),
                                     firmware=device_config.configuration.firmware,
                                     client=client,
                                     device_id=device_config.id)

    def create_inverter_component(component_config: GoodWeInverterSetup):
        nonlocal client
        return inverter.GoodWeInverter(component_config=component_config,
                                       modbus_id=device_config.configuration.modbus_id,
                                       version=GoodWeVersion(device_config.configuration.version),
                                       firmware=device_config.configuration.firmware,
                                       client=client)

    def update_components(components: Iterable[good_we_component_classes]):
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
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=GoodWe)
