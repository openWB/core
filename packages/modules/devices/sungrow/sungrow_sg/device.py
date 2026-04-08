#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common import modbus
from modules.devices.sungrow.sungrow_sg.config import SungrowSG, SungrowSGCounterSetup, SungrowSGInverterSetup
from modules.devices.sungrow.sungrow_sg.counter import SungrowSGCounter
from modules.devices.sungrow.sungrow_sg.inverter import SungrowSGInverter

log = logging.getLogger(__name__)


def create_device(device_config: SungrowSG):
    client = None

    def create_counter_component(component_config: SungrowSGCounterSetup):
        nonlocal client
        return SungrowSGCounter(component_config, device_config=device_config, client=client)

    def create_inverter_component(component_config: SungrowSGInverterSetup):
        nonlocal client
        return SungrowSGInverter(component_config, device_config=device_config, client=client)

    def update_components(components: Iterable[Union[SungrowSGCounter, SungrowSGInverter]]):
        with client:
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
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=SungrowSG)
