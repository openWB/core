# !/usr/bin/env python3
from enum import IntEnum
from typing import Any, Callable, Iterable, Union
from pymodbus.constants import Endian
import functools
import logging

from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.devices.kostal.kostal_plenticore.bat import KostalPlenticoreBat
from modules.devices.kostal.kostal_plenticore.inverter import KostalPlenticoreInverter
from modules.devices.kostal.kostal_plenticore.config import (KostalPlenticore, KostalPlenticoreBatSetup,
                                                             KostalPlenticoreCounterSetup,
                                                             KostalPlenticoreInverterSetup)
from modules.devices.kostal.kostal_plenticore.counter import KostalPlenticoreCounter


log = logging.getLogger(__name__)


class LegacyCounterPosition(IntEnum):
    HOME_CONSUMPTION = 0
    GRID = 1


def update(
        components: Iterable[Union[KostalPlenticoreBat, KostalPlenticoreCounter, KostalPlenticoreInverter]],
        reader: Callable[[int, modbus.ModbusDataType], Any],
        set_inverter_state: bool = True):
    battery = next((component for component in components if isinstance(component, KostalPlenticoreBat)), None)
    bat_state = battery.read_state(reader) if battery else None
    for component in components:
        if isinstance(component, KostalPlenticoreInverter):
            # Fürs erste nur die WR-Werte nutzen ohne Verlustberechnung.
            # power: R575(inverter generation power (actual))
            # exported: R320 (Total yield)
            inverter_state = component.read_state(reader)
            pv_state = inverter_state
            if set_inverter_state:
                component.update(pv_state)
        elif isinstance(component, KostalPlenticoreCounter):
            component.update(reader)
    if bat_state:
        battery.update(bat_state)
    if set_inverter_state is False:
        return pv_state


def create_device(device_config: KostalPlenticore):
    def create_bat_component(component_config: KostalPlenticoreBatSetup):
        return KostalPlenticoreBat(device_config.id, component_config)

    def create_counter_component(component_config: KostalPlenticoreCounterSetup):
        return KostalPlenticoreCounter(device_config.id, component_config)

    def create_inverter_component(component_config: KostalPlenticoreInverterSetup):
        return KostalPlenticoreInverter(component_config)

    def update_components(
        components: Iterable[Union[KostalPlenticoreBat, KostalPlenticoreCounter, KostalPlenticoreInverter]]
    ):
        with tcp_client:
            update(components, reader)

    try:
        tcp_client = modbus.ModbusTcpClient_(device_config.configuration.ip_address, device_config.configuration.port)
        reader = _create_reader(tcp_client, device_config.configuration.modbus_id)
    except Exception:
        log.exception("Fehler in create_device")
    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component, counter=create_counter_component, inverter=create_inverter_component),
        component_updater=MultiComponentUpdater(update_components),
    )


def _create_reader(tcp_client: modbus.ModbusTcpClient_, modbus_id: int) -> Callable[[int, modbus.ModbusDataType], Any]:
    return functools.partial(tcp_client.read_holding_registers, unit=modbus_id, wordorder=Endian.Little)


device_descriptor = DeviceDescriptor(configuration_factory=KostalPlenticore)
