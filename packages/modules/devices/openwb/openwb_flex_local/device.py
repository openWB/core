#!/usr/bin/env python3
import logging
from pathlib import Path
from typing import Iterable

from helpermodules.utils.run_command import run_command
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

    def error_handler():
        run_command([f"{Path(__file__).resolve().parents[4]}/modules/common/restart_protoss_admin"])

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        error_handler=error_handler,
        component_factory=ComponentFactoryByType(
            consumption_counter=create_consumption_counter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=FlexLocalSetup)
