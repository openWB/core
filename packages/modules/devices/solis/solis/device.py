#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.solis.solis.bat import SolisBat
from modules.devices.solis.solis.counter import SolisCounter
from modules.devices.solis.solis.inverter import SolisInverter
from modules.devices.solis.solis.config import Solis, SolisBatSetup, SolisCounterSetup, SolisInverterSetup
from modules.devices.solis.solis.version import SolisVersion

log = logging.getLogger(__name__)


def create_device(device_config: Solis):
    def create_bat_component(component_config: SolisBatSetup):
        return SolisBat(component_config)

    def create_counter_component(component_config: SolisCounterSetup):
        return SolisCounter(component_config, SolisVersion(device_config.configuration.version))

    def create_inverter_component(component_config: SolisInverterSetup):
        return SolisInverter(component_config, SolisVersion(device_config.configuration.version))

    def update_components(components: Iterable[Union[SolisBat, SolisCounter, SolisInverter]]):
        with client as c:
            for component in components:
                with SingleComponentUpdateContext(component.fault_state):
                    component.update(c)

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


device_descriptor = DeviceDescriptor(configuration_factory=Solis)
