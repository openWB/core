#!/usr/bin/env python3
from typing import Any, TypedDict

from pymodbus.constants import Endian

from modules.devices.carlo_gavazzi.carlo_gavazzi.config import CarloGavazziCounterSetup
from modules.common import modbus
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store


class KwargsDict(TypedDict):
    device_id: int
    tcp_client: modbus.ModbusTcpClient_
    modbus_id: int


class CarloGavazziCounter(AbstractCounter):
    def __init__(self, component_config: CarloGavazziCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['tcp_client']
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        with self.__tcp_client:
            voltages = [val / 10 for val in self.__tcp_client.read_input_registers(
                0x00, [ModbusDataType.INT_32] * 3, wordorder=Endian.Little, unit=self.__modbus_id)]
            powers = [val / 10 for val in self.__tcp_client.read_input_registers(
                0x12, [ModbusDataType.INT_32] * 3, wordorder=Endian.Little, unit=self.__modbus_id)]
            power = sum(powers)
            currents = [(val / 1000) for val in self.__tcp_client.read_input_registers(
                0x0C, [ModbusDataType.INT_32] * 3, wordorder=Endian.Little, unit=self.__modbus_id)]
            frequency = self.__tcp_client.read_input_registers(0x33, ModbusDataType.INT_16, unit=self.__modbus_id) / 10
            if frequency > 100:
                frequency = frequency / 10

        imported, exported = self.sim_counter.sim_count(power)

        counter_state = CounterState(
            voltages=voltages,
            currents=currents,
            powers=powers,
            imported=imported,
            exported=exported,
            power=power,
            frequency=frequency
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=CarloGavazziCounterSetup)
