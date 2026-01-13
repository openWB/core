#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.kostal.kostal_piko_ci.config import KostalPikoCiCounterSetup


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class KostalPikoCiCounter(AbstractCounter):
    def __init__(self, component_config: KostalPikoCiCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id

        power = self.client.read_holding_registers(252, ModbusDataType.FLOAT_32, unit=unit)
        powers = [self.client.read_holding_registers(
            reg, ModbusDataType.FLOAT_32, unit=unit) for reg in [224, 234, 244]]
        frequency = self.client.read_holding_registers(220, ModbusDataType.FLOAT_32, unit=unit)
        imported, exported = self.sim_counter.sim_count(power)

        counter_state = CounterState(
            power=power,
            powers=powers,
            frequency=frequency,
            imported=imported,
            exported=exported,
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=KostalPikoCiCounterSetup)
