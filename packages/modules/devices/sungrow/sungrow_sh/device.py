#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common import modbus
from modules.devices.sungrow.sungrow_sh.bat import SungrowSHBat
from modules.devices.sungrow.sungrow_sh.config import SungrowSH, SungrowSHBatSetup
from modules.devices.sungrow.sungrow_sh.config import SungrowSHCounterSetup, SungrowSHInverterSetup
from modules.devices.sungrow.sungrow_sh.counter import SungrowSHCounter
from modules.devices.sungrow.sungrow_sh.inverter import SungrowSHInverter

log = logging.getLogger(__name__)


def create_device(device_config: SungrowSH):
    client = None

    def create_bat_component(component_config: SungrowSHBatSetup):
        nonlocal client
        return SungrowSHBat(component_config, device_config=device_config, client=client)

    def create_counter_component(component_config: SungrowSHCounterSetup):
        nonlocal client
        return SungrowSHCounter(component_config, device_config=device_config, client=client)

    def create_inverter_component(component_config: SungrowSHInverterSetup):
        nonlocal client
        return SungrowSHInverter(component_config, device_config=device_config, client=client)

    def update_components(components: Iterable[Union[SungrowSHBat, SungrowSHCounter, SungrowSHInverter]]):
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


device_descriptor = DeviceDescriptor(configuration_factory=SungrowSH)
