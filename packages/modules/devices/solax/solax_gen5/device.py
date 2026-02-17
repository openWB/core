#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.solax.solax_gen5.bat import SolaxGen5Bat
from modules.devices.solax.solax_gen5.config import SolaxGen5, SolaxGen5BatSetup, SolaxGen5CounterSetup
from modules.devices.solax.solax_gen5.config import SolaxGen5InverterSetup
from modules.devices.solax.solax_gen5.counter import SolaxGen5Counter
from modules.devices.solax.solax_gen5.inverter import SolaxGen5Inverter

log = logging.getLogger(__name__)


def create_device(device_config: SolaxGen5):
    def create_bat_component(component_config: SolaxGen5BatSetup):
        return SolaxGen5Bat(device_config.id, component_config, client, device_config.configuration.modbus_id)

    def create_counter_component(component_config: SolaxGen5CounterSetup):
        return SolaxGen5Counter(device_config.id, component_config, client, device_config.configuration.modbus_id)

    def create_inverter_component(component_config: SolaxGen5InverterSetup):
        return SolaxGen5Inverter(device_config.id, component_config, client, device_config.configuration.modbus_id)

    def update_components(components: Iterable[Union[SolaxGen5Bat, SolaxGen5Counter, SolaxGen5Inverter]]):
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update()

    try:
        client = ModbusTcpClient_(device_config.configuration.ip_address, device_config.configuration.port)
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


device_descriptor = DeviceDescriptor(configuration_factory=SolaxGen5)
