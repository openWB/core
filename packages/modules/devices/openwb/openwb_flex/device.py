#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.openwb.openwb_flex.bat import BatKitFlex
from modules.devices.openwb.openwb_flex.config import (BatKitFlexSetup,
                                                       ConsumptionCounterFlexSetup,
                                                       EvuKitFlexSetup,
                                                       Flex,
                                                       PvKitFlexSetup)
from modules.devices.openwb.openwb_flex.consumption_counter import ConsumptionCounterFlex
from modules.devices.openwb.openwb_flex.counter import EvuKitFlex
from modules.devices.openwb.openwb_flex.inverter import PvKitFlex

log = logging.getLogger(__name__)


def create_device(device_config: Flex):
    client = None

    def create_bat_component(component_config: BatKitFlexSetup):
        nonlocal client
        return BatKitFlex(component_config, device_id=device_config.id, client=client)

    def create_counter_component(component_config: EvuKitFlexSetup):
        nonlocal client
        return EvuKitFlex(component_config, device_id=device_config.id, client=client)

    def create_consumption_counter_component(component_config: ConsumptionCounterFlexSetup):
        nonlocal client
        return ConsumptionCounterFlex(component_config, device_id=device_config.id, client=client)

    def create_inverter_component(component_config: PvKitFlexSetup):
        nonlocal client
        return PvKitFlex(component_config, device_id=device_config.id, client=client)

    def update_components(components: Iterable[Union[BatKitFlex, ConsumptionCounterFlex, EvuKitFlex, PvKitFlex]]):
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
            consumption_counter=create_consumption_counter_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Flex)
