#!/usr/bin/env python3
from typing import Any, TypedDict

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, Endian, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.anker.anker_solix.config import AnkerCounterSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class AnkerCounter(AbstractCounter):
    def __init__(self, component_config: AnkerCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.COUNTER, self.component_config.id, self.fault_state)

    def update(self):
        unit = self.component_config.configuration.modbus_id

        power = self.client.read_input_registers(10644, ModbusDataType.INT_32,
                                                 wordorder=Endian.Little, unit=unit) * -1
        powers = self.client.read_input_registers(10638, [ModbusDataType.INT_32] * 3,
                                                  wordorder=Endian.Little, unit=unit)
        voltages = self.client.read_input_registers(10632, [ModbusDataType.UINT_16] * 3,
                                                    wordorder=Endian.Little, unit=unit)
        currents = self.client.read_input_registers(10666, [ModbusDataType.INT_16] * 3,
                                                    wordorder=Endian.Little, unit=unit)

        voltages = [value / 10 for value in voltages]
        currents = [value / -100 for value in currents]

        self.peak_filter.check_values(power)
        imported, exported = self.sim_counter.sim_count(power)
        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            powers=powers,
            voltages=voltages,
            currents=currents
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=AnkerCounterSetup)
