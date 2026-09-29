#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.fox_ess.fox_ess_h3_smart.bat import FoxEssH3SmartBat
from modules.devices.fox_ess.fox_ess_h3_smart.counter import FoxEssH3SmartCounter
from modules.devices.fox_ess.fox_ess_h3_smart.inverter import FoxEssH3SmartInverter
from modules.devices.fox_ess.fox_ess_h3_smart.config import FoxEssH3Smart, FoxEssH3SmartBatSetup
from modules.devices.fox_ess.fox_ess_h3_smart.config import FoxEssH3SmartCounterSetup, FoxEssH3SmartInverterSetup

log = logging.getLogger(__name__)


def create_device(device_config: FoxEssH3Smart):
    client = None

    def create_bat_component(component_config: FoxEssH3SmartBatSetup):
        return FoxEssH3SmartBat(component_config, device_id=device_config.id, client=client)

    def create_counter_component(component_config: FoxEssH3SmartCounterSetup):
        return FoxEssH3SmartCounter(component_config, device_id=device_config.id, client=client)

    def create_inverter_component(component_config: FoxEssH3SmartInverterSetup):
        return FoxEssH3SmartInverter(component_config, device_id=device_config.id, client=client)

    def update_components(components: Iterable[Union[FoxEssH3SmartBat, FoxEssH3SmartCounter, FoxEssH3SmartInverter]]):
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
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


device_descriptor = DeviceDescriptor(configuration_factory=FoxEssH3Smart)
