#!/usr/bin/env python3
import logging
from typing import Iterable

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.siemens.siemens_sentron.config import SiemensSentron, SiemensSentronCounterSetup
from modules.devices.siemens.siemens_sentron.counter import SiemensSentronCounter

log = logging.getLogger(__name__)


def create_device(device_config: SiemensSentron):
    def create_counter_component(component_config: SiemensSentronCounterSetup):
        return SiemensSentronCounter(component_config, client, device_config.configuration.modbus_id)

    def update_components(components: Iterable[SiemensSentronCounter]):
        with client:
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
            counter=create_counter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=SiemensSentron)
