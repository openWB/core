#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.varta.varta.config import VartaBatModbusSetup


class KwargsDict(TypedDict):
    device_id: int
    modbus_id: int
    client: ModbusTcpClient_


class VartaBatModbus(AbstractBat):
    def __init__(self, component_config: VartaBatModbusSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        self.set_state(self.get_state())

    def get_state(self) -> BatState:
        soc = self.client.read_holding_registers(1068, ModbusDataType.INT_16, unit=self.__modbus_id)
        power = self.client.read_holding_registers(1066, ModbusDataType.INT_16, unit=self.__modbus_id)
        return BatState(
            power=power,
            soc=soc,
        )

    def set_state(self, state: BatState) -> None:
        state.imported, state.exported = self.sim_counter.sim_count(state.power)
        self.store.set(state)


component_descriptor = ComponentDescriptor(configuration_factory=VartaBatModbusSetup)
