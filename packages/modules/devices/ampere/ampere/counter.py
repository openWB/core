#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.ampere.ampere.config import AmpereCounterSetup


class KwargsDict(TypedDict):
    device_id: int
    modbus_id: int
    client: ModbusTcpClient_


class AmpereCounter(AbstractCounter):
    def __init__(self,
                 component_config: AmpereCounterSetup,
                 **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.modbus_id: int = self.kwargs['modbus_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        powers = self.client.read_input_registers(1349, [ModbusDataType.INT_16]*3, unit=self.modbus_id)
        power = self.client.read_input_registers(1348, ModbusDataType.INT_16, unit=self.modbus_id)

        imported, exported = self.sim_counter.sim_count(power)

        counter_state = CounterState(
            powers=powers,
            imported=imported,
            exported=exported,
            power=power
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=AmpereCounterSetup)
