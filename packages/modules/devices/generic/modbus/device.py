#!/usr/bin/env python3
from typing import Iterable, Union
import logging

from helpermodules.broker import BrokerClient
from helpermodules.utils.topic_parser import decode_payload
from modules.devices.generic.modbus.bat import GenericModbusBat
from modules.devices.generic.modbus.inverter import GenericModbusInverter
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_type import type_to_topic_mapping
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.generic.modbus.counter import GenericModbusCounter

from modules.devices.generic.modbus.config import GenericModbus, GenericModbusCounterSetup, GenericModbusBatSetup, GenericModbusInverterSetup

from modules.common import modbus

log = logging.getLogger(__name__)


def create_device(device_config: GenericModbus):
    client = None

    def create_counter_component(component_config: GenericModbusCounterSetup):
        nonlocal client
        return GenericModbusCounter(component_config, device_id=device_config.id, client=client)

    def create_bat_component(component_config: GenericModbusBatSetup):
        nonlocal client
        return GenericModbusBat(component_config, device_id=device_config.id, client=client)

    def create_inverter_component(component_config: GenericModbusInverterSetup):
        nonlocal client
        return GenericModbusInverter(component_config, device_id=device_config.id, client=client)

    def update_components(components: Iterable[Union[GenericModbusCounter, GenericModbusBat, GenericModbusInverter]]):
        for component in components:
            with SingleComponentUpdateContext(component.fault_state):
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


device_descriptor = DeviceDescriptor(configuration_factory=GenericModbus)
