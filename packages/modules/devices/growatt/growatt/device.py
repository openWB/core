#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.growatt.growatt.bat import GrowattBat
from modules.devices.growatt.growatt.config import Growatt, GrowattBatSetup, GrowattCounterSetup, GrowattInverterSetup
from modules.devices.growatt.growatt.counter import GrowattCounter
from modules.devices.growatt.growatt.inverter import GrowattInverter
from modules.devices.growatt.growatt.version import GrowattVersion

log = logging.getLogger(__name__)


def create_device(device_config: Growatt):
    def create_bat_component(component_config: GrowattBatSetup):
        return GrowattBat(component_config,
                          device_config.configuration.modbus_id,
                          GrowattVersion(device_config.configuration.version))

    def create_counter_component(component_config: GrowattCounterSetup):
        return GrowattCounter(component_config,
                              device_config.configuration.modbus_id,
                              GrowattVersion(device_config.configuration.version))

    def create_inverter_component(component_config: GrowattInverterSetup):
        return GrowattInverter(component_config,
                               device_config.configuration.modbus_id,
                               GrowattVersion(device_config.configuration.version))

    def update_components(components: Iterable[Union[GrowattBat, GrowattCounter, GrowattInverter]]):
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


device_descriptor = DeviceDescriptor(configuration_factory=Growatt)
