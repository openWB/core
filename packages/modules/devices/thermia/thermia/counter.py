#!/usr/bin/env python3
from typing import TypedDict, Any
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.thermia.thermia.config import ThermiaCounterSetup
from pymodbus.constants import Endian


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_
    modbus_id: int


class ThermiaCounter(AbstractCounter):
    def __init__(self, component_config: ThermiaCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.modbus_id: int = self.kwargs['modbus_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        with self.client:
            voltages = [val / 100 for val in self.client.read_input_registers(
                72, [ModbusDataType.INT_16] * 3, unit=self.modbus_id)]
            powers = [val / 1 for val in self.client.read_input_registers(
                78, [ModbusDataType.INT_16] * 3, unit=self.modbus_id)]
            power = sum(powers)
            currents = [(val / 100) for val in self.client.read_input_registers(
                69, [ModbusDataType.INT_16] * 3, unit=self.modbus_id)]
            imported = self.client.read_input_registers(
                83, ModbusDataType.INT_32, wordorder=Endian.Little,
                unit=self.modbus_id) * 100
            exported = 0

        counter_state = CounterState(
            currents=currents,
            imported=imported,
            exported=exported,
            power=power,
            powers=powers,
            voltages=voltages
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=ThermiaCounterSetup)
