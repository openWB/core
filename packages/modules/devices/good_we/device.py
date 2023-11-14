#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.good_we.bat import GoodWeBat
from modules.devices.good_we.config import (GoodWe, GoodWeBatSetup, GoodWeCounterSetup,
                                            GoodWeInverterSetup)
from modules.devices.good_we.counter import GoodWeCounter
from modules.devices.good_we.inverter import GoodWeInverter
from modules.devices.good_we.version import GoodWeVersion

log = logging.getLogger(__name__)

good_we_component_classes = Union[GoodWeBat, GoodWeCounter, GoodWeInverter]


def create_device(device_config: GoodWe):
    def create_bat_component(component_config: GoodWeBatSetup):
        return GoodWeBat(device_config.id, component_config, client, version)

    def create_counter_component(component_config: GoodWeCounterSetup):
        return GoodWeCounter(device_config.id, component_config, client)

    def create_inverter_component(component_config: GoodWeInverterSetup):
        return GoodWeInverter(device_config.id, component_config, client)

    def update_components(components: Iterable[good_we_component_classes]):
        with client as c:
            for component in components:
                with SingleComponentUpdateContext(component.component_info):
                    component.update(c)

    try:
        version = GoodWeVersion(device_config.configuration.version)
        client = modbus.ModbusTcpClient_(device_config.configuration.ip_address, 502)
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
