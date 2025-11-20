#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_counter_value_store
from modules.devices.orno.orno.config import OrnoCounterSetup


class KwargsDict(TypedDict):
    client: ModbusTcpClient_


class OrnoCounter(AbstractCounter):
    def __init__(self, component_config: OrnoCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        power = self.client.read_holding_registers(
            0x141, ModbusDataType.INT_32, device_id=self.component_config.configuration.modbus_id)
        imported = self.client.read_holding_registers(
            0xA001, ModbusDataType.INT_32, device_id=self.component_config.configuration.modbus_id) * 10

        counter_state = CounterState(
            imported=imported,
            exported=0,
            power=power,
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=OrnoCounterSetup)
