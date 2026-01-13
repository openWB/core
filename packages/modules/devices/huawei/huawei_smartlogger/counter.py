#!/usr/bin/env python3
from typing import TypedDict, Any
from modules.common import modbus
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.huawei.huawei_smartlogger.config import Huawei_SmartloggerCounterSetup


class KwargsDict(TypedDict):
    device_id: int
    tcp_client: modbus.ModbusTcpClient_


class Huawei_SmartloggerCounter(AbstractCounter):
    def __init__(self, component_config: Huawei_SmartloggerCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: modbus.ModbusTcpClient_ = self.kwargs['tcp_client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        modbus_id = self.component_config.configuration.modbus_id
        power = self.client.read_holding_registers(32278, ModbusDataType.INT_32, unit=modbus_id)
        currents = [val / 10 for val in self.client.read_holding_registers(
            32272, [ModbusDataType.INT_32] * 3, unit=modbus_id)]
        voltages = [val / 100 for val in self.client.read_holding_registers(
            32260, [ModbusDataType.INT_32] * 3, unit=modbus_id)]
        powers = self.client.read_holding_registers(32335, [ModbusDataType.INT_32] * 3, unit=modbus_id)
        imported, exported = self.sim_counter.sim_count(power)
        counter_state = CounterState(
            currents=currents,
            imported=imported,
            exported=exported,
            power=power,
            powers=powers,
            voltages=voltages
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=Huawei_SmartloggerCounterSetup)
