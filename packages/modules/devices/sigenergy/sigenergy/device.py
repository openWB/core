#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.sigenergy.sigenergy.bat import SigenergyBat
from modules.devices.sigenergy.sigenergy.counter import SigenergyCounter
from modules.devices.sigenergy.sigenergy.inverter import SigenergyInverter
from modules.devices.sigenergy.sigenergy.config import (
    Sigenergy,
    SigenergyBatSetup,
    SigenergyCounterSetup,
    SigenergyInverterSetup,
)

log = logging.getLogger(__name__)


def create_device(device_config: Sigenergy):
    client = None

    def create_bat_component(component_config: SigenergyBatSetup):
        nonlocal client
        return SigenergyBat(component_config, device_id=device_config.id, client=client)

    def create_counter_component(component_config: SigenergyCounterSetup):
        nonlocal client
        return SigenergyCounter(component_config, device_id=device_config.id, client=client)

    def create_inverter_component(component_config: SigenergyInverterSetup):
        nonlocal client
        return SigenergyInverter(component_config, device_id=device_config.id, client=client)

    def update_components(components: Iterable[Union[SigenergyBat, SigenergyCounter, SigenergyInverter]]):
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
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Sigenergy)
