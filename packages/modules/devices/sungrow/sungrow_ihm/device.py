#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common import modbus
from modules.devices.sungrow.sungrow_ihm.bat import SungrowIHMBat
from modules.devices.sungrow.sungrow_ihm.config import SungrowIHM, SungrowIHMBatSetup
from modules.devices.sungrow.sungrow_ihm.config import SungrowIHMCounterSetup, SungrowIHMInverterSetup
from modules.devices.sungrow.sungrow_ihm.counter import SungrowIHMCounter
from modules.devices.sungrow.sungrow_ihm.inverter import SungrowIHMInverter

log = logging.getLogger(__name__)


def create_device(device_config: SungrowIHM):
    client = None

    def create_bat_component(component_config: SungrowIHMBatSetup):
        nonlocal client
        return SungrowIHMBat(component_config, device_config=device_config, client=client)

    def create_counter_component(component_config: SungrowIHMCounterSetup):
        nonlocal client
        return SungrowIHMCounter(component_config, device_config=device_config, client=client)

    def create_inverter_component(component_config: SungrowIHMInverterSetup):
        nonlocal client
        return SungrowIHMInverter(component_config, device_config=device_config, client=client)

    def update_components(components: Iterable[Union[SungrowIHMBat, SungrowIHMCounter, SungrowIHMInverter]]):
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
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=SungrowIHM)
