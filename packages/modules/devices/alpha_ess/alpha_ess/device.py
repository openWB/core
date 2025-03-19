#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.alpha_ess.alpha_ess.config import (
    AlphaEss, AlphaEssBatSetup, AlphaEssCounterSetup, AlphaEssInverterSetup)
from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.devices.alpha_ess.alpha_ess import bat
from modules.devices.alpha_ess.alpha_ess import counter
from modules.devices.alpha_ess.alpha_ess import inverter

log = logging.getLogger(__name__)


alpha_ess_component_classes = Union[bat.AlphaEssBat, counter.AlphaEssCounter, inverter.AlphaEssInverter]


def create_device(device_config: AlphaEss):
    def create_bat_component(component_config: AlphaEssBatSetup):
        return bat.AlphaEssBat(device_config.id,
                               component_config,
                               client,
                               device_config.configuration,
                               device_config.configuration.modbus_id)

    def create_counter_component(component_config: AlphaEssCounterSetup):
        return counter.AlphaEssCounter(device_config.id,
                                       component_config,
                                       client,
                                       device_config.configuration,
                                       device_config.configuration.modbus_id)

    def create_inverter_component(component_config: AlphaEssInverterSetup):
        return inverter.AlphaEssInverter(device_config.id,
                                         component_config,
                                         client,
                                         device_config.configuration,
                                         device_config.configuration.modbus_id)

    def update_components(components: Iterable[Union[alpha_ess_component_classes]]):
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update()

    try:
        if device_config.configuration.source == 0:
            client = modbus.ModbusTcpClient_("192.168.193.125", 8899)
        else:
            client = modbus.ModbusTcpClient_(
                device_config.configuration.ip_address, device_config.configuration.port)
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


device_descriptor = DeviceDescriptor(configuration_factory=AlphaEss)
