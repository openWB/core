#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.modbus import ModbusTcpClient_
from modules.devices.qcells.bat import QCellsBat
from modules.devices.qcells.config import QCells, QCellsBatSetup, QCellsCounterSetup, QCellsInverterSetup
from modules.devices.qcells.counter import QCellsCounter
from modules.devices.qcells.inverter import QCellsInverter

log = logging.getLogger(__name__)


def create_device(device_config: QCells):
    def create_bat_component(component_config: QCellsBatSetup):
        return QCellsBat(component_config,
                         device_config.configuration.modbus_id)

    def create_counter_component(component_config: QCellsCounterSetup):
        return QCellsCounter(component_config,
                             device_config.configuration.modbus_id)

    def create_inverter_component(component_config: QCellsInverterSetup):
        return QCellsInverter(component_config,
                              device_config.configuration.modbus_id)

    def update_components(components: Iterable[Union[QCellsBat, QCellsCounter, QCellsInverter]]):
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


device_descriptor = DeviceDescriptor(configuration_factory=QCells)
