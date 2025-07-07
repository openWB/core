#!/usr/bin/env python3
import logging

from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, IndependentComponentUpdater
from modules.devices.tasmota.tasmota.config import Tasmota, TasmotaCounterSetup, TasmotaInverterSetup, TasmotaBatSetup
from modules.common.abstract_device import DeviceDescriptor
from modules.devices.tasmota.tasmota.counter import TasmotaCounter
from modules.devices.tasmota.tasmota.inverter import TasmotaInverter
from modules.devices.tasmota.tasmota.bat import TasmotaBat

log = logging.getLogger(__name__)


def create_device(device_config: Tasmota):
    def create_counter_component(component_config: TasmotaCounterSetup):
        return TasmotaCounter(component_config,
                              device_id=device_config.id,
                              ip_address=device_config.configuration.ip_address)
# phase=int(device_config.configuration.phase)

    def create_inverter_component(component_config: TasmotaInverterSetup):
        return TasmotaInverter(component_config,
                               device_id=device_config.id,
                               ip_address=device_config.configuration.ip_address)

    def create_bat_component(component_config: TasmotaBatSetup):
        return TasmotaBat(component_config,
                          device_id=device_config.id,
                          ip_address=device_config.configuration.ip_address)

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            counter=create_counter_component,
            inverter=create_inverter_component,
            bat=create_bat_component
        ),
        component_updater=IndependentComponentUpdater(lambda component: component.update())
    )


device_descriptor = DeviceDescriptor(configuration_factory=Tasmota)
