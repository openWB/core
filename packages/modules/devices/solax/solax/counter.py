#!/usr/bin/env python3
from typing import Any, TypedDict
from pymodbus.constants import Endian

from modules.common import modbus
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.store import get_counter_value_store
from modules.devices.solax.solax.config import SolaxCounterSetup, Solax
from modules.devices.solax.solax.version import SolaxVersion


class KwargsDict(TypedDict):
    client: modbus.ModbusTcpClient_
    device_config: Solax


class SolaxCounter(AbstractCounter):
    def __init__(self, component_config: SolaxCounterSetup, **kwargs: Any) -> None:
        self.component_config = SolaxCounterSetup(**component_config)
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__tcp_client = self.kwargs['client']
        self.device_config = self.kwargs['device_config']
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        unit = self.device_config.configuration.modbus_id

        if SolaxVersion(self.device_config.configuration.version) == SolaxVersion.G2:
            power = self.__tcp_client.read_input_registers(
                0x043B, ModbusDataType.INT_32, wordorder=Endian.Little, unit=unit) * -1
            frequency = self.__tcp_client.read_input_registers(0x0407, ModbusDataType.UINT_16, unit=unit) / 100
            powers = [-value for value in self.__tcp_client.read_input_registers(
                0x0704, [ModbusDataType.INT_32] * 3, wordorder=Endian.Little, unit=unit)]
            exported, imported = [value * 10 for value in self.__tcp_client.read_input_registers(
                0x043D, [ModbusDataType.UINT_32] * 2, wordorder=Endian.Little, unit=unit)]

        elif SolaxVersion(self.device_config.configuration.version) == SolaxVersion.G3:
            power = self.__tcp_client.read_input_registers(
                0x0046, ModbusDataType.INT_32, wordorder=Endian.Little, unit=unit) * -1
            frequency = self.__tcp_client.read_input_registers(0x0007, ModbusDataType.UINT_16, unit=unit) / 100
            try:
                powers = [-value for value in self.__tcp_client.read_input_registers(
                    0x0082, [ModbusDataType.INT_32] * 3, wordorder=Endian.Little, unit=unit)]
            except Exception:
                powers = None
            exported, imported = [value * 10 for value in self.__tcp_client.read_input_registers(
                0x0048, [ModbusDataType.UINT_32] * 2, wordorder=Endian.Little, unit=unit)]

        else:
            power = self.__tcp_client.read_input_registers(
                0x0409, ModbusDataType.INT_32, wordorder=Endian.Little, unit=unit) * -1
            frequency = self.__tcp_client.read_input_registers(0x0406, ModbusDataType.UINT_16, unit=unit) / 100
            powers = None
            exported, imported = [value * 100 for value in self.__tcp_client.read_input_registers(
                0x042F, [ModbusDataType.UINT_32] * 2, wordorder=Endian.Little, unit=unit)]

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            powers=powers,
            frequency=frequency
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SolaxCounterSetup)
