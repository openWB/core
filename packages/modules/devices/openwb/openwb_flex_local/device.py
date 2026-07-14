#!/usr/bin/env python3
import logging
from typing import Iterable

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusSerialClient_
from modules.devices.openwb.openwb_flex_local.config import FlexLocalSetup, LocalConsumptionCounterSetup
from modules.devices.openwb.openwb_flex_local.consumption_counter import LocalConsumptionCounter

log = logging.getLogger(__name__)


def create_device(device_config: FlexLocalSetup):
    client = None

    def create_consumption_counter_component(component_config: LocalConsumptionCounterSetup):
        return LocalConsumptionCounter(component_config, device_id=device_config.id, client=client)

    def update_components(components: Iterable[LocalConsumptionCounter]):
        for component in components:
            with SingleComponentUpdateContext(component.fault_state):
                component.update()

    def initializer():
        nonlocal client
        client = ModbusSerialClient_(device_config.configuration.port)

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            consumption_counter=create_consumption_counter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=FlexLocalSetup)
