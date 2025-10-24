#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.deye.deye.config import DeyeCounterSetup
from modules.devices.deye.deye.device_type import DeviceType


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class DeyeCounter(AbstractCounter):
    def __init__(self, component_config: DeyeCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.device_type = DeviceType(self.client.read_holding_registers(
            0, ModbusDataType.INT_16, unit=self.component_config.configuration.modbus_id))

    def update(self):
        unit = self.component_config.configuration.modbus_id

        if self.device_type == DeviceType.SINGLE_PHASE_STRING or self.device_type == DeviceType.SINGLE_PHASE_HYBRID:
            frequency = self.client.read_holding_registers(79, ModbusDataType.INT_16, unit=unit) / 100

            if self.device_type == DeviceType.SINGLE_PHASE_HYBRID:
                powers = [0]*3
                currents = [0]*3
                voltages = [0]*3
                power = [0]
                imported, exported = self.sim_counter.sim_count(power)

            elif self.device_type == DeviceType.SINGLE_PHASE_STRING:
                currents = [
                    c / 100 for c in self.client.read_holding_registers(76, [ModbusDataType.INT_16]*3, unit=unit)]
                voltages = [
                    v / 10 for v in self.client.read_holding_registers(70, [ModbusDataType.INT_16]*3, unit=unit)]
                powers = [currents[i] * voltages[i] for i in range(0, 3)]
                power = sum(powers)
                imported, exported = self.sim_counter.sim_count(power)

        else:  # THREE_PHASE_LV (0x0500, 0x0005), THREE_PHASE_HV (0x0006)
            currents = [c / 100 for c in self.client.read_holding_registers(613, [ModbusDataType.INT_16]*3, unit=unit)]
            voltages = [v / 10 for v in self.client.read_holding_registers(644, [ModbusDataType.INT_16]*3, unit=unit)]
            powers = self.client.read_holding_registers(616, [ModbusDataType.INT_16]*3, unit=unit)
            power = sum(powers)
            imported, exported = self.sim_counter.sim_count(power)

        counter_state = CounterState(
            currents=currents,
            voltages=voltages,
            powers=powers,
            power=power,
            imported=imported,
            exported=exported
        )
        if 'frequency' in locals():
            counter_state.frequency = frequency
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=DeyeCounterSetup)
