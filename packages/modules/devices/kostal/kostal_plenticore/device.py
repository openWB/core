#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.kostal.kostal_plenticore.bat import KostalPlenticoreBat
from modules.devices.kostal.kostal_plenticore.counter import KostalPlenticoreCounter
from modules.devices.kostal.kostal_plenticore.inverter import KostalPlenticoreInverter
from modules.devices.kostal.kostal_plenticore.config import KostalPlenticore, KostalPlenticoreBatSetup
from modules.devices.kostal.kostal_plenticore.config import KostalPlenticoreCounterSetup, KostalPlenticoreInverterSetup

log = logging.getLogger(__name__)


def create_device(device_config: KostalPlenticore):
    client = None

    def create_bat_component(component_config: KostalPlenticoreBatSetup):
        nonlocal client
        return KostalPlenticoreBat(component_config,
                                   device_id=device_config.id,
                                   modbus_id=device_config.configuration.modbus_id,
                                   client=client)

    def create_counter_component(component_config: KostalPlenticoreCounterSetup):
        nonlocal client
        return KostalPlenticoreCounter(component_config,
                                       device_id=device_config.id,
                                       modbus_id=device_config.configuration.modbus_id,
                                       client=client)

    def create_inverter_component(component_config: KostalPlenticoreInverterSetup):
        nonlocal client
        return KostalPlenticoreInverter(component_config,
                                        device_id=device_config.id,
                                        modbus_id=device_config.configuration.modbus_id,
                                        client=client)

    def update_components(
            components: Iterable[Union[KostalPlenticoreBat, KostalPlenticoreCounter, KostalPlenticoreInverter]]):
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


device_descriptor = DeviceDescriptor(configuration_factory=KostalPlenticore)
