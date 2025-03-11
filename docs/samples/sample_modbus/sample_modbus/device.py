#!/usr/bin/env python3
import logging
from typing import Iterable,  Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.sample_modbus.sample_modbus.bat import SampleBat
from modules.devices.sample_modbus.sample_modbus.config import Sample, SampleBatSetup, SampleCounterSetup, SampleInverterSetup
from modules.devices.sample_modbus.sample_modbus.counter import SampleCounter
from modules.devices.sample_modbus.sample_modbus.inverter import SampleInverter

log = logging.getLogger(__name__)


def create_device(device_config: Sample):
    client = None

    def create_bat_component(component_config: SampleBatSetup):
        nonlocal client
        return SampleBat(component_config, device_id=device_config.id, client=client)

    def create_counter_component(component_config: SampleCounterSetup):
        nonlocal client
        return SampleCounter(component_config, device_id=device_config.id, client=client)

    def create_inverter_component(component_config: SampleInverterSetup):
        nonlocal client
        return SampleInverter(component_config, device_id=device_config.id, client=client)

    def update_components(components: Iterable[Union[SampleBat, SampleCounter, SampleInverter]]):
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
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Sample)
