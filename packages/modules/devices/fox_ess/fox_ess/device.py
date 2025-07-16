#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.fox_ess.fox_ess.bat import FoxEssBat
from modules.devices.fox_ess.fox_ess.counter import FoxEssCounter
from modules.devices.fox_ess.fox_ess.inverter import FoxEssInverter
from modules.devices.fox_ess.fox_ess.config import FoxEss, FoxEssBatSetup, FoxEssCounterSetup, FoxEssInverterSetup

log = logging.getLogger(__name__)


def create_device(device_config: FoxEss):
    client = None

    def create_bat_component(component_config: FoxEssBatSetup):
        nonlocal client
        return FoxEssBat(component_config=component_config, client=client)

    def create_counter_component(component_config: FoxEssCounterSetup):
        nonlocal client
        return FoxEssCounter(component_config=component_config, client=client)

    def create_inverter_component(component_config: FoxEssInverterSetup):
        nonlocal client
        return FoxEssInverter(component_config=component_config, client=client)

    def update_components(components: Iterable[Union[FoxEssBat, FoxEssCounter, FoxEssInverter]]):
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


device_descriptor = DeviceDescriptor(configuration_factory=FoxEss)
