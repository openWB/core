#!/usr/bin/env python3
from typing import TypedDict, Any
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.sigenergy.sigenergy.config import SigenergyCounterSetup


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class SigenergyCounter:
    def __init__(self, component_config: SigenergyCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)

    def update(self):
        unit = self.component_config.configuration.modbus_id

        powers = self.client.read_holding_registers(30052, [ModbusDataType.INT_32]*3, unit=unit)
        power = self.client.read_holding_registers(30005, ModbusDataType.INT_32, unit=unit)
        imported, exported = self.sim_counter.sim_count(power)

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            powers=powers
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SigenergyCounterSetup)
