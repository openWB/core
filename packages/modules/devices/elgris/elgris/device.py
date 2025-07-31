#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.elgris.elgris import bat, counter, inverter
from modules.devices.elgris.elgris.config import Elgris, ElgrisBatSetup, ElgrisCounterSetup
from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.devices.elgris.elgris.config import ElgrisInverterSetup

log = logging.getLogger(__name__)


def create_device(device_config: Elgris):
    client = None

    def create_bat_component(component_config: ElgrisBatSetup):
        nonlocal client
        return bat.ElgrisBat(component_config=component_config, tcp_client=client,
                             modbus_id=device_config.configuration.modbus_id)

    def create_counter_component(component_config: ElgrisCounterSetup):
        nonlocal client
        return counter.ElgrisCounter(component_config=component_config, tcp_client=client,
                                     modbus_id=device_config.configuration.modbus_id)

    def create_inverter_component(component_config: ElgrisInverterSetup):
        nonlocal client
        return inverter.ElgrisInverter(component_config=component_config, tcp_client=client,
                                       modbus_id=device_config.configuration.modbus_id)

    def update_components(components: Iterable[Union[bat.ElgrisBat, counter.ElgrisCounter, inverter.ElgrisInverter]]):
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update()

    def initializer():
        nonlocal client
        client = modbus.ModbusTcpClient_(device_config.configuration.ip_address, device_config.configuration.port)

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Elgris)
