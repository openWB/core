#!/usr/bin/env python3
import logging
from typing import Iterable

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusSerialClient_
from modules.devices.openwb.openwb_flex_local.config import FlexLocalSetup, LocalConsumptionCounterSetup
from modules.devices.openwb.openwb_flex_local.consumption_counter import LocalConsumptionCounter
from modules.common.serial_modbus_devices import get_serial_modbus_devices, BUS_SOURCES

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

        device, count = get_serial_modbus_devices()
        if count == 1 and device[0] in BUS_SOURCES:
            port = device[0]
            log.debug(f"Verbrauchszähler mit lokaler Auslesung nutzt Port {port}")
            client = ModbusSerialClient_(port)
        else:
            port = "UNKNOWN"
            log.debug(f"Verbrauchszähler mit lokaler Auslesung konnte Port nicht ermitteln, gefundene Ports: {device}")
            client = None

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            consumption_counter=create_consumption_counter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=FlexLocalSetup)
