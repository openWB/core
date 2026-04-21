#!/usr/bin/env python3
import logging
from typing import Union, Iterable

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common import modbus
from modules.devices.e3dc.e3dc.bat import E3dcBat
from modules.devices.e3dc.e3dc.inverter import E3dcInverter
from modules.devices.e3dc.e3dc.external_inverter import E3dcExternalInverter
from modules.devices.e3dc.e3dc.counter import E3dcCounter
from modules.devices.e3dc.e3dc.config import E3dc
from modules.devices.e3dc.e3dc.config import E3dcBatSetup
from modules.devices.e3dc.e3dc.config import E3dcCounterSetup
from modules.devices.e3dc.e3dc.config import E3dcInverterSetup, E3dcExternalInverterSetup


log = logging.getLogger(__name__)


def create_device(device_config: E3dc) -> ConfigurableDevice:
    client = None

    def create_bat_component(component_config: E3dcBatSetup) -> E3dcBat:
        nonlocal client
        return E3dcBat(component_config=component_config,
                       device_id=device_config.id,
                       modbus_id=device_config.configuration.modbus_id,
                       client=client)

    def create_counter_component(component_config: E3dcCounterSetup) -> E3dcCounter:
        nonlocal client
        return E3dcCounter(component_config=component_config,
                           device_id=device_config.id,
                           modbus_id=device_config.configuration.modbus_id,
                           client=client)

    def create_inverter_component(component_config: E3dcInverterSetup) -> E3dcInverter:
        nonlocal client
        return E3dcInverter(component_config=component_config,
                            device_id=device_config.id,
                            modbus_id=device_config.configuration.modbus_id,
                            client=client)

    def create_external_inverter_component(component_config: E3dcExternalInverterSetup) -> E3dcExternalInverter:
        nonlocal client
        return E3dcExternalInverter(component_config=component_config,
                                    device_id=device_config.id,
                                    modbus_id=device_config.configuration.modbus_id,
                                    client=client)

    def update_components(components: Iterable[Union[E3dcBat, E3dcCounter, E3dcInverter,
                                                     E3dcExternalInverter]]) -> None:
        nonlocal client
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update()

    def initializer():
        nonlocal client
        client = modbus.ModbusTcpClient_(device_config.configuration.address, device_config.configuration.port)
    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
            external_inverter=create_external_inverter_component
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=E3dc)
