#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
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
    def create_bat_component(component_config: BatKitFlexSetup):
        return BatKitFlex(device_config.id, component_config, client)

    def create_counter_component(component_config: EvuKitFlexSetup):
        return EvuKitFlex(device_config.id, component_config, client)

    def create_consumption_counter_component(component_config: ConsumptionCounterFlexSetup):
        return ConsumptionCounterFlex(device_config.id, component_config, client)

    def create_inverter_component(component_config: PvKitFlexSetup):
        return PvKitFlex(device_config.id, component_config, client)

    def update_components(components: Iterable[Union[BatKitFlex, ConsumptionCounterFlex, EvuKitFlex, PvKitFlex]]):
        for component in components:
            with SingleComponentUpdateContext(component.fault_state):
                component.update()

    try:
        client = ModbusTcpClient_(device_config.configuration.ip_address, device_config.configuration.port)
    except Exception:
        log.exception("Fehler in create_device")
    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            consumption_counter=create_consumption_counter_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Flex)
