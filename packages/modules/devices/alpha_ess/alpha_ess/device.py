#!/usr/bin/env python3
import logging
from pathlib import Path
from typing import Iterable, Union

from helpermodules.utils.run_command import run_command
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.alpha_ess.alpha_ess.config import (
    AlphaEss, AlphaEssBatSetup, AlphaEssCounterSetup, AlphaEssInverterSetup)
from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.devices.alpha_ess.alpha_ess import bat
from modules.devices.alpha_ess.alpha_ess import counter
from modules.devices.alpha_ess.alpha_ess import inverter

log = logging.getLogger(__name__)


alpha_ess_component_classes = Union[bat.AlphaEssBat, counter.AlphaEssCounter, inverter.AlphaEssInverter]


def create_device(device_config: AlphaEss):
    client = None

    def create_bat_component(component_config: AlphaEssBatSetup):
        nonlocal client
        return bat.AlphaEssBat(component_config,
                               device_id=device_config.id,
                               tcp_client=client,
                               modbus_id=device_config.configuration.modbus_id)

    def create_counter_component(component_config: AlphaEssCounterSetup):
        nonlocal client
        return counter.AlphaEssCounter(component_config,
                                       tcp_client=client,
                                       device_config=device_config.configuration,
                                       modbus_id=device_config.configuration.modbus_id)

    def create_inverter_component(component_config: AlphaEssInverterSetup):
        nonlocal client
        return inverter.AlphaEssInverter(component_config=component_config,
                                         device_id=device_config.id,
                                         tcp_client=client,
                                         device_config=device_config.configuration,
                                         modbus_id=device_config.configuration.modbus_id)

    def update_components(components: Iterable[Union[alpha_ess_component_classes]]):
        nonlocal client
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state, update_always=False):
                    component.update()

    def initializer():
        nonlocal client
        if device_config.configuration.source == 0:
            client = modbus.ModbusTcpClient_("192.168.193.125", 8899)
        else:
            client = modbus.ModbusTcpClient_(
                device_config.configuration.ip_address, device_config.configuration.port)

    def error_handler():
        run_command(f"{Path(__file__).resolve().parents[4]}/modules/common/restart_protoss_admin")

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        error_handler=error_handler,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=AlphaEss)
