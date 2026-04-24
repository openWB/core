#!/usr/bin/env python3
import time
from typing import Any, TypedDict

from modules.devices.alpha_ess.alpha_ess.config import AlphaEssConfiguration, AlphaEssCounterSetup
from modules.common import modbus
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.store import get_counter_value_store
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType


class KwargsDict(TypedDict):
    tcp_client: modbus.ModbusTcpClient_
    device_config: AlphaEssConfiguration
    modbus_id: int


class AlphaEssCounter(AbstractCounter):
    def __init__(self, component_config: AlphaEssCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['tcp_client']
        self.__device_config: AlphaEssConfiguration = self.kwargs['device_config']
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.COUNTER, self.component_config.id, self.fault_state)

    def update(self):
        time.sleep(0.1)
        if self.__device_config.source == 0 and self.__device_config.version == 0:
            power, exported, imported = self.__tcp_client.read_holding_registers(
                0x6, [modbus.ModbusDataType.INT_32] * 3, unit=self.__modbus_id)
            exported *= 10
            imported *= 10
            imported, exported = self.peak_filter.check_values(power, imported, exported)
            currents = [val / 230 for val in self.__tcp_client.read_holding_registers(
                0x0000, [ModbusDataType.INT_32]*3, unit=self.__modbus_id)]
            counter_state = CounterState(
                currents=currents,
                imported=imported,
                exported=exported,
                power=power
            )
        else:
            power = self.__tcp_client.read_holding_registers(0x0021, ModbusDataType.INT_32, unit=self.__modbus_id)
            exported, imported = [
                val * 10 for val in self.__tcp_client.read_holding_registers(
                    0x0010, [ModbusDataType.INT_32] * 2, unit=self.__modbus_id
                )]
            imported, exported = self.peak_filter.check_values(power, imported, exported)
            frequency = self.__tcp_client.read_holding_registers(
                0x001A, ModbusDataType.UINT_16, unit=self.__modbus_id) / 100
            currents = self.__tcp_client.read_holding_registers(
                0x0017, [ModbusDataType.INT_16]*3, unit=self.__modbus_id)
            powers = self.__tcp_client.read_holding_registers(
                0x001b, [ModbusDataType.INT_32]*3, unit=self.__modbus_id)
            currents = scale_currents(currents, powers)
            counter_state = CounterState(
                currents=currents,
                imported=imported,
                exported=exported,
                power=power,
                powers=powers,
                frequency=frequency
            )
        self.store.set(counter_state)


def scale_currents(currents, powers):
    factors = [-1000, -100, -10, 10, 100, 1000]
    scaled_currents = []
    for c, p in zip(currents, powers):
        if p == 0:
            scaled_currents.append(0)
        else:
            factor = c * 230 / p
            rounded_factor = min(factors, key=lambda z: abs(factor - z))
            scaled_currents.append(c / rounded_factor)

    return scaled_currents


component_descriptor = ComponentDescriptor(configuration_factory=AlphaEssCounterSetup)
