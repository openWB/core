#!/usr/bin/env python3
import logging
from typing import Iterable

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.azzurro_zcs.azzurro_zcs_3p.config import ZCS3P, ZCSPvInverterSetup
from modules.devices.azzurro_zcs.azzurro_zcs_3p.pv_inverter import ZCSPvInverter

log = logging.getLogger(__name__)


def create_device(device_config: ZCS3P):
    client = None

    def create_pv_inverter_component(component_config: ZCSPvInverterSetup):
        nonlocal client
        return ZCSPvInverter(component_config=component_config,
                             modbus_id=device_config.configuration.modbus_id,
                             client=client)

    def update_components(components: Iterable[ZCSPvInverter]):
        nonlocal client
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update()

    def initializer():
        nonlocal client
        client = ModbusTcpClient_(device_config.configuration.ip_address, device_config.configuration.port)

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            pv_inverter=create_pv_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=ZCS3P)
