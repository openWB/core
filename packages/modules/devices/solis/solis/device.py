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

log = logging.getLogger(__name__)


def create_device(device_config: Solis):
    client = None

    def create_bat_component(component_config: SolisBatSetup):
        return SolisBat(component_config,
                        client=client,
                        device_id=device_config.id,
                        version=device_config.configuration.version)

    def create_counter_component(component_config: SolisCounterSetup):
        return SolisCounter(component_config, client=client, version=device_config.configuration.version)

    def create_inverter_component(component_config: SolisInverterSetup):
        return SolisInverter(component_config,
                             client=client,
                             device_id=device_config.id,
                             version=device_config.configuration.version)

    def update_components(components: Iterable[Union[SolisBat, SolisCounter, SolisInverter]]):
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
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(
    configuration_factory=Solis,
    compatibility_device_note="Benötigt einen Solis Datalogger, der auch Modbus TCP-fähig ist.\nWelcher Datalogger "
    "für einen speziellen Wechselrichtertyp benötigt wird, kann der Solis Support beantworten."
)
