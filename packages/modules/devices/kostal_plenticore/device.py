# !/usr/bin/env python3
from enum import IntEnum
from ipparser import ipparser
from itertools import chain
from typing import Any, Callable, Iterable, List, Union
from pymodbus.constants import Endian
import functools
import logging

from helpermodules.cli import run_using_positional_cli_args
from modules.common import modbus
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import InverterState
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.common.store import get_counter_value_store
from modules.devices.kostal_plenticore.bat import KostalPlenticoreBat
from modules.devices.kostal_plenticore.inverter import KostalPlenticoreInverter
from modules.devices.kostal_plenticore.config import (KostalPlenticore, KostalPlenticoreBatSetup,
                                                      KostalPlenticoreCounterSetup, KostalPlenticoreInverterSetup)
from modules.devices.kostal_plenticore.counter import KostalPlenticoreCounter


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


def read_legacy_inverter(ip1: str, ip2: str, battery: int, ip3: str) -> InverterState:
    # in IP3 kann ein aufeinanderfolgende Liste enthalten sein "192.168.0.1-3"
    log.debug("Kostal Plenticore: WR1: %s, WR2: %s, WR3: %s, Battery: %s", ip1, ip2, ip3, battery)
    inverter_component = KostalPlenticoreInverter(KostalPlenticoreInverterSetup(id=1))

    def get_hybrid_inverter_state(ip: str) -> InverterState:
        battery_component = KostalPlenticoreBat(1, KostalPlenticoreBatSetup())
        with modbus.ModbusTcpClient_(ip, 1502) as client:
            return update(
                [inverter_component, battery_component], _create_reader(client, 71), set_inverter_state=False
            )

    def get_standard_inverter_state(ip: str) -> InverterState:
        with modbus.ModbusTcpClient_(ip, 1502) as client:
            return inverter_component.read_state(_create_reader(client, 71))

    def inverter_state_sum(a: InverterState, b: InverterState) -> InverterState:
        return InverterState(exported=a.exported + b.exported, power=a.power + b.power)

    inverter_state = functools.reduce(
        inverter_state_sum,
        map(get_standard_inverter_state, filter("none".__ne__, chain([ip2], ipparser(ip3)))),
        get_hybrid_inverter_state(ip1) if battery else get_standard_inverter_state(ip1)
    )
    inverter_component.update(inverter_state)
    return inverter_state


def read_legacy_counter(ip1: str, ip2: str, battery: int, ip3: str, position: int) -> None:
    log.debug("Kostal Plenticore: WR1: %s, Position: %s", ip1, position)
    client = modbus.ModbusTcpClient_(ip1, 1502)
    reader = _create_reader(client, 71)
    counter_component = KostalPlenticoreCounter(None, KostalPlenticoreCounterSetup(id=None))
    if LegacyCounterPosition(position) == LegacyCounterPosition.GRID:
        with client:
            counter_component.update(reader)
    else:
        with client:
            counter_state = counter_component.get_values(reader)
            bat_power = KostalPlenticoreBat(None, KostalPlenticoreBatSetup()).read_state(reader).power
        inverter_power = read_legacy_inverter(ip1, ip2, battery, ip3).power
        counter_state.power += inverter_power + bat_power
        counter_state = counter_component.update_imported_exported(counter_state)
        get_counter_value_store(None).set(counter_state)


def main(argv: List[str]):
    run_using_positional_cli_args({"counter": read_legacy_counter, "inverter": read_legacy_inverter}, argv
                                  )


device_descriptor = DeviceDescriptor(configuration_factory=KostalPlenticore)
