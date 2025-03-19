#!/usr/bin/env python3
import logging

from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, IndependentComponentUpdater
from modules.devices.tasmota.tasmota.config import Tasmota, TasmotaCounterSetup
from modules.common.abstract_device import DeviceDescriptor
from modules.devices.tasmota.tasmota.counter import TasmotaCounter

log = logging.getLogger(__name__)


def create_device(device_config: Tasmota):
    def create_counter_component(component_config: TasmotaCounterSetup):
        return TasmotaCounter(device_config.id,
                              component_config,
                              device_config.configuration.ip_address,
                              int(device_config.configuration.phase))

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            counter=create_counter_component,
        ),
        component_updater=IndependentComponentUpdater(lambda component: component.update())
    )


device_descriptor = DeviceDescriptor(configuration_factory=Tasmota)
