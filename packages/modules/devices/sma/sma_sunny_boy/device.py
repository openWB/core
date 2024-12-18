#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.sma.sma_sunny_boy.bat import SunnyBoyBat
from modules.devices.sma.sma_sunny_boy.bat_smart_energy import SunnyBoySmartEnergyBat
from modules.devices.sma.sma_sunny_boy.bat_tesvolt import TesvoltBat
from modules.devices.sma.sma_sunny_boy.config import (SmaSunnyBoy, SmaSunnyBoyBatSetup, SmaSunnyBoyCounterSetup,
                                                      SmaSunnyBoyInverterSetup, SmaSunnyBoySmartEnergyBatSetup,
                                                      SmaTesvoltBatSetup)
from modules.devices.sma.sma_sunny_boy.counter import SmaSunnyBoyCounter
from modules.devices.sma.sma_sunny_boy.inverter import SmaSunnyBoyInverter

log = logging.getLogger(__name__)


sma_modbus_tcp_component_classes = Union[
    SunnyBoyBat,
    SunnyBoySmartEnergyBat,
    SmaSunnyBoyCounter,
    SmaSunnyBoyInverter
]


def create_device(device_config: SmaSunnyBoy):
    def create_bat_component(component_config: SmaSunnyBoyBatSetup):
        return SunnyBoyBat(device_config.id, component_config, client)

    def create_bat_smart_energy_component(component_config: SmaSunnyBoySmartEnergyBatSetup):
        return SunnyBoySmartEnergyBat(device_config.id, component_config, client)

    def create_bat_tesvolt_component(component_config: SmaTesvoltBatSetup):
        return TesvoltBat(device_config.id, component_config, client)

    def create_counter_component(component_config: SmaSunnyBoyCounterSetup):
        return SmaSunnyBoyCounter(device_config.id, component_config, client)

    def create_inverter_component(component_config: SmaSunnyBoyInverterSetup):
        return SmaSunnyBoyInverter(device_config.id, component_config, client)

    def update_components(components: Iterable[sma_modbus_tcp_component_classes]):
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
            bat=create_bat_component,
            bat_smart_energy=create_bat_smart_energy_component,
            bat_tesvolt=create_bat_tesvolt_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=SmaSunnyBoy)
