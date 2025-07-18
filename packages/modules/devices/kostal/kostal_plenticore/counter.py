#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.kostal.kostal_plenticore.config import KostalPlenticoreCounterSetup


class KwargsDict(TypedDict):
    device_id: int
    modbus_id: int
    client: ModbusTcpClient_


class KostalPlenticoreCounter(AbstractCounter):
    def __init__(self, component_config: KostalPlenticoreCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.modbus_id: int = self.kwargs['modbus_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")

    def update(self) -> None:
        power = self.client.read_holding_registers(252, ModbusDataType.FLOAT_32, unit=self.modbus_id)
        imported, exported = self.sim_counter.sim_count(power)
        power_factor = self.client.read_holding_registers(150, ModbusDataType.FLOAT_32, unit=self.modbus_id)
        currents = [
                self.client.read_holding_registers(
                    222, ModbusDataType.FLOAT_32, unit=self.modbus_id),
                self.client.read_holding_registers(
                    232, ModbusDataType.FLOAT_32, unit=self.modbus_id),
                self.client.read_holding_registers(
                    242, ModbusDataType.FLOAT_32, unit=self.modbus_id)]
        voltages = [
                self.client.read_holding_registers(
                    230, ModbusDataType.FLOAT_32, unit=self.modbus_id),
                self.client.read_holding_registers(
                    240, ModbusDataType.FLOAT_32, unit=self.modbus_id),
                self.client.read_holding_registers(
                    250, ModbusDataType.FLOAT_32, unit=self.modbus_id)]
        powers = [
                self.client.read_holding_registers(
                    224, ModbusDataType.FLOAT_32, unit=self.modbus_id),
                self.client.read_holding_registers(
                    234, ModbusDataType.FLOAT_32, unit=self.modbus_id),
                self.client.read_holding_registers(
                    244, ModbusDataType.FLOAT_32, unit=self.modbus_id)]
        frequency = self.client.read_holding_registers(220, ModbusDataType.FLOAT_32, unit=self.modbus_id)

        counter_state = CounterState(
            powers=powers,
            currents=currents,
            voltages=voltages,
            power=power,
            power_factors=[power_factor]*3,
            frequency=frequency,
            imported=imported,
            exported=exported
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=KostalPlenticoreCounterSetup)
