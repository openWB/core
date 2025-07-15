#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.azzurro_zcs.azzurro_zcs.bat import ZCSBat
from modules.devices.azzurro_zcs.azzurro_zcs.config import ZCS, ZCSBatSetup, ZCSCounterSetup, ZCSInverterSetup
from modules.devices.azzurro_zcs.azzurro_zcs.counter import ZCSCounter
from modules.devices.azzurro_zcs.azzurro_zcs.inverter import ZCSInverter

log = logging.getLogger(__name__)


def create_device(device_config: ZCS):
    client = None

    def create_bat_component(component_config: ZCSBatSetup):
        nonlocal client
        return ZCSBat(component_config=component_config, modbus_id=device_config.configuration.modbus_id, client=client)

    def create_counter_component(component_config: ZCSCounterSetup):
        nonlocal client
        return ZCSCounter(component_config=component_config,
                          modbus_id=device_config.configuration.modbus_id,
                          client=client)

    def create_inverter_component(component_config: ZCSInverterSetup):
        nonlocal client
        return ZCSInverter(component_config=component_config,
                           modbus_id=device_config.configuration.modbus_id,
                           client=client)

    def update_components(components: Iterable[Union[ZCSBat, ZCSCounter, ZCSInverter]]):
        nonlocal client
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state, update_always=False):
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


device_descriptor = DeviceDescriptor(configuration_factory=ZCS)
