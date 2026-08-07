#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.devices.deye.deye_solarman.counter import DeyeSolarmanCounter
from modules.devices.deye.deye_solarman.inverter import DeyeSolarmanInverter
from modules.devices.deye.deye_solarman.bat import DeyeSolarmanBat
from modules.devices.deye.deye_solarman.config import (DeyeSolarman, DeyeSolarmanCounterSetup,
                                                       DeyeSolarmanInverterSetup, DeyeSolarmanBatSetup)
from pysolarmanv5 import PySolarmanV5 as ModbusSolarmanClient_

log = logging.getLogger(__name__)


def create_device(device_config: DeyeSolarman):
    client = None

    def create_bat_component(component_config: DeyeSolarmanBatSetup):
        return DeyeSolarmanBat(component_config=component_config, device_id=device_config.id, client=client)

    def create_counter_component(component_config: DeyeSolarmanCounterSetup):
        return DeyeSolarmanCounter(component_config=component_config, device_id=device_config.id, client=client)

    def create_inverter_component(component_config: DeyeSolarmanInverterSetup):
        return DeyeSolarmanInverter(component_config=component_config, device_id=device_config.id, client=client)

    def update_components(components: Iterable[Union[DeyeSolarmanBat, DeyeSolarmanCounter, DeyeSolarmanInverter]]):
        for component in components:
            with SingleComponentUpdateContext(component.fault_state):
                component.update()

    def initializer():
        nonlocal client
        client = ModbusSolarmanClient_(device_config.configuration.ip_address,
                                       device_config.configuration.serial,
                                       port=device_config.configuration.port,
                                       mb_slave_id=device_config.configuration.modbus_id,
                                       auto_reconnect=True)

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


device_descriptor = DeviceDescriptor(configuration_factory=DeyeSolarman)
