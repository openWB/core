#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.kaco.kaco_nh.bat import KacoNHBat
from modules.devices.kaco.kaco_nh.config import (KacoNH, KacoNHBatSetup,
                                                 KacoNHCounterSetup, KacoNHInverterSetup)
from modules.devices.kaco.kaco_nh.counter import KacoNHCounter
from modules.devices.kaco.kaco_nh.inverter import KacoNHInverter

log = logging.getLogger(__name__)


def create_device(device_config: KacoNH):
    def create_bat_component(component_config: KacoNHBatSetup):
        return KacoNHBat(component_config=component_config,
                         device_id=device_config.id,
                         device_config=device_config.configuration)

    def create_counter_component(component_config: KacoNHCounterSetup):
        return KacoNHCounter(component_config=component_config,
                             device_id=device_config.id,
                             device_config=device_config.configuration)

    def create_inverter_component(component_config: KacoNHInverterSetup):
        return KacoNHInverter(component_config=component_config,
                              device_id=device_config.id,
                              device_config=device_config.configuration)

    def update_components(components: Iterable[Union[KacoNHBat, KacoNHCounter, KacoNHInverter]]):
        for component in components:
            component.update()

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=KacoNH)
