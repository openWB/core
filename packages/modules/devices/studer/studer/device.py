#!/usr/bin/env python3
""" Modul zum Auslesen von Alpha Ess Speichern, Zählern und Wechselrichtern.
"""
import logging
from typing import Iterable, Union

from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.studer.studer.bat import StuderBat
from modules.devices.studer.studer.config import Studer, StuderBatSetup, StuderInverterSetup
from modules.devices.studer.studer.inverter import StuderInverter

log = logging.getLogger(__name__)


def create_device(device_config: Studer):
    def create_bat_component(component_config: StuderBatSetup):
        return StuderBat(component_config, client)

    def create_inverter_component(component_config: StuderInverterSetup):
        return StuderInverter(component_config, client)

    def update_components(components: Iterable[Union[StuderBat, StuderInverter]]):
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
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Studer)
