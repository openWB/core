#!/usr/bin/env python3
from typing import Dict, Union
from pymodbus.constants import Endian

from dataclass_utils import dataclass_from_dict
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_counter_value_store
from modules.devices.azzurro_zcs.azzurro_zcs.config import ZCSCounterSetup


class ZCSCounter(AbstractCounter):
    def __init__(self,
                 component_config: Union[Dict, ZCSCounterSetup],
                 modbus_id: int,
                 client: ModbusTcpClient_) -> None:
        self.component_config = dataclass_from_dict(ZCSCounterSetup, component_config)
        self.__modbus_id = modbus_id
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.client = client

    def update(self) -> None:
        # 0x0212 Grid Power Int16 -10-10 kW Unit 0,01kW Feed in/out power
        # 0x0214 Input/Output power Int16 -10-10kW 0,01kW Energy storage power inverter
        power = self.client.read_input_registers(0x0212, ModbusDataType.INT_16, wordorder=Endian.Little,
                                                 unit=self.__modbus_id) * -1
        # 0x020C Grid frequency UInt 0-100 Hz Unit 0,01 Hz
        frequency = self.client.read_input_registers(
            0x020C, ModbusDataType.UINT_16, unit=self.__modbus_id) / 100
        exported = [value * 10
                    for value in self.client.read_input_registers(
                        # 0x021E Total energy injected into the grid UInt16 Unit 1kWh high
                        # 0x021F Total energy injected into the grid UInt16 Unit 1kWh low
                        0x021E, [ModbusDataType.UINT_16] * 10,
                        wordorder=Endian.Little, unit=self.__modbus_id)]
        imported = [value * 10
                    for value in self.client.read_input_registers(
                        # 0x0220 Total energy taken from the grid UInt16 Unit 1kWh high
                        # 0x0221 Total energy taken from the grid UInt16 Unit 1kWh low
                        0x0220, [ModbusDataType.UINT_16] * 10,
                        wordorder=Endian.Little, unit=self.__modbus_id)]

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            frequency=frequency,
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=ZCSCounterSetup)
