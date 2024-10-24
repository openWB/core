#!/usr/bin/env python3
import logging
from typing import Iterable

from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.carlo_gavazzi.carlo_gavazzi import counter
from modules.devices.carlo_gavazzi.carlo_gavazzi.config import CarloGavazzi, CarloGavazziCounterSetup
from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext

log = logging.getLogger(__name__)


def create_device(device_config: CarloGavazzi):
    def create_counter_component(component_config: CarloGavazziCounterSetup):
        return counter.CarloGavazziCounter(device_config.id, component_config, client,
                                           device_config.configuration.modbus_id)

    def update_components(components: Iterable[counter.CarloGavazziCounter]):
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update()

    try:
        client = modbus.ModbusTcpClient_(device_config.configuration.ip_address, device_config.configuration.port)
    except Exception:
        log.exception("Fehler in create_device")
    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            counter=create_counter_component
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=CarloGavazzi)
