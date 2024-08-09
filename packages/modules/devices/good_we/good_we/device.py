#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.good_we.good_we import bat
from modules.devices.good_we.good_we import counter
from modules.devices.good_we.good_we import inverter
from modules.devices.good_we.good_we.config import GoodWe, GoodWeBatSetup, GoodWeCounterSetup, GoodWeInverterSetup

log = logging.getLogger(__name__)

good_we_component_classes = Union[bat.GoodWeBat, counter.GoodWeCounter, inverter.GoodWeInverter]


def create_device(device_config: GoodWe):
    def create_bat_component(component_config: GoodWeBatSetup):
        return bat.GoodWeBat(device_config.configuration.modbus_id,
                             device_config.configuration.version, device_config.configuration.firmware,
                             component_config, client)

    def create_counter_component(component_config: GoodWeCounterSetup):
        return counter.GoodWeCounter(device_config.id, device_config.configuration.modbus_id,
                                     device_config.configuration.version, device_config.configuration.firmware,
                                     component_config, client)

    def create_inverter_component(component_config: GoodWeInverterSetup):
        return inverter.GoodWeInverter(device_config.configuration.modbus_id,
                                       device_config.configuration.version, device_config.configuration.firmware,
                                       component_config, client)

    def update_components(components: Iterable[good_we_component_classes]):
        with client:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update()

    try:
        client = modbus.ModbusTcpClient_(device_config.configuration.ip_address, device_config.configuration.port)
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


device_descriptor = DeviceDescriptor(configuration_factory=GoodWe)
