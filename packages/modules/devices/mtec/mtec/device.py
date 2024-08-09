#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.mtec.mtec.bat import MTecBat
from modules.devices.mtec.mtec.counter import MTecCounter
from modules.devices.mtec.mtec.inverter import MTecInverter
from modules.devices.mtec.mtec.config import MTec, MTecBatSetup, MTecCounterSetup, MTecInverterSetup

log = logging.getLogger(__name__)


def create_device(device_config: MTec):
    def create_bat_component(component_config: MTecBatSetup):
        return MTecBat(device_config.id, component_config)

    def create_counter_component(component_config: MTecCounterSetup):
        return MTecCounter(device_config.id, component_config)

    def create_inverter_component(component_config: MTecInverterSetup):
        return MTecInverter(device_config.id, component_config)

    def update_components(components: Iterable[Union[MTecBat, MTecCounter, MTecInverter]]):
        with client as c:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update(c)

    try:
        client = ModbusTcpClient_(device_config.configuration.ip_address, device_config.configuration.port)
    except Exception:
        log.exception("Fehler in create_device")
    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=MTec)
