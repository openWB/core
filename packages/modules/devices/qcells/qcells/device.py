#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.qcells.qcells.bat import QCellsBat
from modules.devices.qcells.qcells.config import QCells, QCellsBatSetup, QCellsCounterSetup, QCellsInverterSetup
from modules.devices.qcells.qcells.counter import QCellsCounter
from modules.devices.qcells.qcells.inverter import QCellsInverter

log = logging.getLogger(__name__)


def create_device(device_config: QCells):
    client = None

    def create_bat_component(component_config: QCellsBatSetup):
        nonlocal client
        return QCellsBat(component_config, modbus_id=device_config.configuration.modbus_id, client=client)

    def create_counter_component(component_config: QCellsCounterSetup):
        nonlocal client
        return QCellsCounter(component_config, modbus_id=device_config.configuration.modbus_id, client=client)

    def create_inverter_component(component_config: QCellsInverterSetup):
        nonlocal client
        return QCellsInverter(component_config, modbus_id=device_config.configuration.modbus_id, client=client)

    def update_components(components: Iterable[Union[QCellsBat, QCellsCounter, QCellsInverter]]):
        nonlocal client
        with client:
            for component in components:
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


device_descriptor = DeviceDescriptor(configuration_factory=QCells)
