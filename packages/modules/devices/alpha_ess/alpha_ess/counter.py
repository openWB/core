#!/usr/bin/env python3
import time
from typing import Callable, Any, TypedDict

from modules.devices.alpha_ess.alpha_ess.config import AlphaEssConfiguration, AlphaEssCounterSetup
from modules.common import modbus
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.store import get_counter_value_store


class KwargsDict(TypedDict):
    tcp_client: modbus.ModbusTcpClient_
    device_config: AlphaEssConfiguration
    modbus_id: int


class AlphaEssCounter(AbstractCounter):
    def __init__(self, component_config: AlphaEssCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['tcp_client']
        self.__device_config: AlphaEssConfiguration = self.kwargs['device_config']
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        time.sleep(0.1)
        counter_state = self.__get_values_factory()
        self.store.set(counter_state)

    def __get_values_factory(self) -> Callable[[int], CounterState]:
        if self.__device_config.source == 0 and self.__device_config.version == 0:
            return self.__get_values_before_v123
        else:
            return self.__get_values_since_v123

    def __get_values_before_v123(self) -> CounterState:
        power, exported, imported = self.__tcp_client.read_holding_registers(
            0x6, [modbus.ModbusDataType.INT_32] * 3, unit=self.__modbus_id)
        exported *= 10
        imported *= 10
        currents = [val / 230 for val in self.__tcp_client.read_holding_registers(
            0x0000, [ModbusDataType.INT_32]*3, unit=self.__modbus_id)]

        counter_state = CounterState(
            currents=currents,
            imported=imported,
            exported=exported,
            power=power
        )
        return counter_state

    def __get_values_since_v123(self) -> CounterState:
        power = self.__tcp_client.read_holding_registers(0x0021, ModbusDataType.INT_32, unit=self.__modbus_id)
        exported, imported = [
            val * 10 for val in self.__tcp_client.read_holding_registers(
                0x0010, [ModbusDataType.INT_32] * 2, unit=self.__modbus_id
            )]
        currents = [val / 1000 for val in self.__tcp_client.read_holding_registers(
            0x0017, [ModbusDataType.INT_16]*3, unit=self.__modbus_id)]

        counter_state = CounterState(
            currents=currents,
            imported=imported,
            exported=exported,
            power=power
        )
        return counter_state


component_descriptor = ComponentDescriptor(
    configuration_factory=AlphaEssCounterSetup)
