#!/usr/bin/env python3
import logging
from typing import Iterable

from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.saxpower.saxpower.bat import SaxpowerBat
from modules.devices.saxpower.saxpower.config import Saxpower, SaxpowerBatSetup

log = logging.getLogger(__name__)


def create_device(device_config: Saxpower):
    def create_bat_component(component_config: SaxpowerBatSetup):
        return SaxpowerBat(device_config.id, component_config, client, device_config.configuration.modbus_id)

    def update_components(components: Iterable[SaxpowerBat]):
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
            bat=create_bat_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Saxpower)
