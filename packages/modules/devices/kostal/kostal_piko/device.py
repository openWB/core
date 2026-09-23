#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common.abstract_device import DeviceDescriptor
from modules.devices.kostal.kostal_piko import counter
from modules.devices.kostal.kostal_piko import inverter
from modules.devices.kostal.kostal_piko import bat
from modules.devices.kostal.kostal_piko.config import (KostalPiko, KostalPikoCounterSetup,
                                                       KostalPikoInverterSetup, KostalPikoBatSetup)

log = logging.getLogger(__name__)


def create_device(device_config: KostalPiko):
    def create_counter_component(component_config: KostalPikoCounterSetup):
        return counter.KostalPikoCounter(component_config,
                                         device_id=device_config.id,
                                         ip_address=device_config.configuration.ip_address)

    def create_inverter_component(component_config: KostalPikoInverterSetup):
        return inverter.KostalPikoInverter(component_config,
                                           ip_address=device_config.configuration.ip_address)

    def create_bat_component(component_config: KostalPikoBatSetup):
        return bat.KostalPikoBat(component_config,
                                 device_id=device_config.id,
                                 ip_address=device_config.configuration.ip_address)

    def update_components(
        components: Iterable[Union[counter.KostalPikoCounter, inverter.KostalPikoInverter, bat.KostalPikoBat]]
    ):
        # Fehler pro Komponente isoliert, statt bei einem Fehler alle als defekt zu markieren.
        for component in components:
            with SingleComponentUpdateContext(component.fault_state):
                component.update()

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            counter=create_counter_component,
            inverter=create_inverter_component,
            bat=create_bat_component
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=KostalPiko)
