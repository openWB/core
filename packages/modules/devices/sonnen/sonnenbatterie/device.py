#!/usr/bin/env python3
""" Modul zum Auslesen von sonnenBatterie Speichern.
"""
import logging

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, IndependentComponentUpdater
from modules.devices.sonnen.sonnenbatterie.bat import SonnenbatterieBat
from modules.devices.sonnen.sonnenbatterie.config import (SonnenBatterie, SonnenbatterieBatSetup,
                                                          SonnenbatterieCounterSetup,
                                                          SonnenbatterieInverterSetup)
from modules.devices.sonnen.sonnenbatterie.counter import SonnenbatterieCounter
from modules.devices.sonnen.sonnenbatterie.inverter import SonnenbatterieInverter


log = logging.getLogger(__name__)


def create_device(device_config: SonnenBatterie):
    def create_bat_component(component_config: SonnenbatterieBatSetup):
        return SonnenbatterieBat(device_config.id,
                                 device_config.configuration.ip_address,
                                 device_config.configuration.variant,
                                 component_config)

    def create_counter_component(component_config: SonnenbatterieCounterSetup):
        return SonnenbatterieCounter(device_config.id,
                                     device_config.configuration.ip_address,
                                     device_config.configuration.variant,
                                     component_config)

    def create_inverter_component(component_config: SonnenbatterieInverterSetup):
        return SonnenbatterieInverter(device_config.id,
                                      device_config.configuration.ip_address,
                                      device_config.configuration.variant,
                                      component_config)

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=IndependentComponentUpdater(lambda component: component.update())
    )


device_descriptor = DeviceDescriptor(configuration_factory=SonnenBatterie)
