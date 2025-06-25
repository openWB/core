#!/usr/bin/env python3
import logging
from modules.common import req

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, IndependentComponentUpdater
from modules.devices.shelly.shelly.inverter import ShellyInverter
from modules.devices.shelly.shelly.bat import ShellyBat
from modules.devices.shelly.shelly.counter import ShellyCounter
from modules.devices.shelly.shelly.config import Shelly, ShellyInverterSetup, ShellyBatSetup, ShellyCounterSetup


log = logging.getLogger(__name__)


def create_device(device_config: Shelly) -> ConfigurableDevice:
    generation = 1

    def create_counter_component(component_config: ShellyCounterSetup) -> ShellyCounter:
        nonlocal generation
        return ShellyCounter(component_config,
                             device_id=device_config.id,
                             ip_address=device_config.configuration.ip_address,
                             factor=device_config.configuration.factor,
                             generation=generation)

    def create_inverter_component(component_config: ShellyInverterSetup) -> ShellyInverter:
        nonlocal generation
        return ShellyInverter(component_config,
                              device_id=device_config.id,
                              ip_address=device_config.configuration.ip_address,
                              factor=device_config.configuration.factor,
                              generation=generation)

    def create_bat_component(component_config: ShellyBatSetup) -> ShellyBat:
        nonlocal generation
        return ShellyBat(component_config,
                         device_id=device_config.id,
                         ip_address=device_config.configuration.ip_address,
                         factor=device_config.configuration.factor,
                         generation=generation)

    def initializer() -> None:
        nonlocal generation
        device_info = req.get_http_session().get(
            f"http://{device_config.configuration.ip_address}/shelly", timeout=3).json()
        if 'gen' in device_info:  # gen 2+
            generation = int(device_info['gen'])

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        # wenn das Auslesen nicht klappt, konnte evlt beim Start die Generation nicht ermittelt werden
        error_handler=initializer,
        component_factory=ComponentFactoryByType(
            counter=create_counter_component,
            inverter=create_inverter_component,
            bat=create_bat_component
        ),
        component_updater=IndependentComponentUpdater(lambda component: component.update())
    )


device_descriptor = DeviceDescriptor(configuration_factory=Shelly)
