#!/usr/bin/env python3
""" Modul zum Auslesen von SonnenBatterie Speichern.
"""
import logging

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, IndependentComponentUpdater
from modules.devices.sonnen.sonnenbatterie.bat import SonnenbatterieBat
from modules.devices.sonnen.sonnenbatterie.config import (SonnenBatterie, SonnenbatterieBatSetup,
                                                          SonnenbatterieCounterSetup,
                                                          SonnenbatterieConsumptionCounterSetup,
                                                          SonnenbatterieInverterSetup)
from modules.devices.sonnen.sonnenbatterie.counter import SonnenbatterieCounter
from modules.devices.sonnen.sonnenbatterie.counter_consumption import SonnenbatterieConsumptionCounter
from modules.devices.sonnen.sonnenbatterie.inverter import SonnenbatterieInverter


log = logging.getLogger(__name__)


def create_device(device_config: SonnenBatterie):
    def create_bat_component(component_config: SonnenbatterieBatSetup):
        return SonnenbatterieBat(component_config,
                                 device_id=device_config.id,
                                 device_address=device_config.configuration.ip_address,
                                 device_variant=device_config.configuration.variant,
                                 device_api_v2_token=device_config.configuration.api_v2_token)

    def create_evu_counter_component(component_config: SonnenbatterieCounterSetup):
        return SonnenbatterieCounter(component_config,
                                     device_id=device_config.id,
                                     device_address=device_config.configuration.ip_address,
                                     device_variant=device_config.configuration.variant,
                                     device_api_v2_token=device_config.configuration.api_v2_token)

    def create_consumption_counter_component(component_config: SonnenbatterieConsumptionCounterSetup):
        return SonnenbatterieConsumptionCounter(component_config,
                                                device_address=device_config.configuration.ip_address,
                                                device_variant=device_config.configuration.variant,
                                                device_api_v2_token=device_config.configuration.api_v2_token)

    def create_inverter_component(component_config: SonnenbatterieInverterSetup):
        return SonnenbatterieInverter(component_config,
                                      device_id=device_config.id,
                                      device_address=device_config.configuration.ip_address,
                                      device_variant=device_config.configuration.variant,
                                      device_api_v2_token=device_config.configuration.api_v2_token)

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_evu_counter_component,
            counter_consumption=create_consumption_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=IndependentComponentUpdater(lambda component: component.update())
    )


device_descriptor = DeviceDescriptor(configuration_factory=SonnenBatterie)
