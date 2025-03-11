#!/usr/bin/env python3
import time
from typing import Callable, Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.devices.alpha_ess.alpha_ess.config import AlphaEssConfiguration, AlphaEssCounterSetup
from modules.common import modbus
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.store import get_counter_value_store


class AlphaEssCounter(AbstractCounter):
    def __init__(self,
                 device_id: int,
                 component_config: Union[Dict, AlphaEssCounterSetup],
                 tcp_client: modbus.ModbusTcpClient_,
                 device_config: AlphaEssConfiguration,
                 modbus_id: int) -> None:
        self.component_config = dataclass_from_dict(AlphaEssCounterSetup, component_config)
        self.__tcp_client = tcp_client
        self.__device_config = device_config
        self.__modbus_id = modbus_id
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        time.sleep(0.1)
        factory_method = self.__get_values_factory()
        counter_state = factory_method(self.__modbus_id)
        self.store.set(counter_state)

    def __get_values_factory(self) -> Callable[[int], CounterState]:
        if self.__device_config.source == 0 and self.__device_config.version == 0:
            return self.__get_values_before_v123
        else:
            return self.__get_values_since_v123

    def __get_values_before_v123(self, unit: int) -> CounterState:
        power, exported, imported = self.__tcp_client.read_holding_registers(
            0x6, [modbus.ModbusDataType.INT_32] * 3, unit=unit)
        exported *= 10
        imported *= 10
        currents = [val / 230 for val in self.__tcp_client.read_holding_registers(
            0x0000, [ModbusDataType.INT_32]*3, unit=unit)]

        counter_state = CounterState(
            currents=currents,
            imported=imported,
            exported=exported,
            power=power
        )
        return counter_state

    def __get_values_since_v123(self, unit: int) -> CounterState:
        power = self.__tcp_client.read_holding_registers(0x0021, ModbusDataType.INT_32, unit=unit)
        exported, imported = [
            val * 10 for val in self.__tcp_client.read_holding_registers(
                0x0010, [ModbusDataType.INT_32] * 2, unit=unit)]
        currents = [val / 1000 for val in self.__tcp_client.read_holding_registers(
            0x0017, [ModbusDataType.INT_16]*3, unit=unit)]

        counter_state = CounterState(
            currents=currents,
            imported=imported,
            exported=exported,
            power=power
        )
        return counter_state


component_descriptor = ComponentDescriptor(
    configuration_factory=AlphaEssCounterSetup)
