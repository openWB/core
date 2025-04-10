#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.siemens.siemens.bat import SiemensBat
from modules.devices.siemens.siemens.config import Siemens, SiemensBatSetup, SiemensCounterSetup, SiemensInverterSetup
from modules.devices.siemens.siemens.counter import SiemensCounter
from modules.devices.siemens.siemens.inverter import SiemensInverter

log = logging.getLogger(__name__)


siemens_component_classes = Union[SiemensBat, SiemensCounter, SiemensInverter]


def create_device(device_config: Siemens):
    client = None

    def create_bat_component(component_config: SiemensBatSetup):
        nonlocal client
        return SiemensBat(component_config,
                          device_id=device_config.id,
                          client=client,
                          modbus_id=device_config.configuration.modbus_id)

    def create_counter_component(component_config: SiemensCounterSetup):
        nonlocal client
        return SiemensCounter(component_config,
                              device_id=device_config.id,
                              client=client,
                              modbus_id=device_config.configuration.modbus_id)

    def create_inverter_component(component_config: SiemensInverterSetup):
        nonlocal client
        return SiemensInverter(component_config,
                               device_id=device_config.id,
                               client=client,
                               modbus_id=device_config.configuration.modbus_id)

    def update_components(components: Iterable[siemens_component_classes]):
        nonlocal client
        with client:
            for component in components:
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
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Siemens)
