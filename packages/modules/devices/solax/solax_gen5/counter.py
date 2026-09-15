#!/usr/bin/env python3
from typing import Dict, Union
from pymodbus.constants import Endian

from dataclass_utils import dataclass_from_dict
from modules.common import modbus
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.store import get_counter_value_store
from modules.devices.solax.solax_gen5.config import SolaxGen5CounterSetup


class SolaxGen5Counter(AbstractCounter):
    def __init__(self,
                 device_id: int,
                 component_config: Union[Dict, SolaxGen5CounterSetup],
                 tcp_client: modbus.ModbusTcpClient_,
                 modbus_id: int) -> None:

        self.component_config = dataclass_from_dict(SolaxGen5CounterSetup, component_config)
        self.__modbus_id = modbus_id
        self.__tcp_client = tcp_client
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        with self.__tcp_client:
            power = self.__tcp_client.read_input_registers(70, ModbusDataType.INT_32, wordorder=Endian.Little, 
                                                           unit=self.__modbus_id) * -1
            frequency = self.__tcp_client.read_input_registers(7, ModbusDataType.UINT_16, unit=self.__modbus_id) / 100
            voltages = [value / 10
                        for value in self.__tcp_client.read_input_registers(
                            202, [ModbusDataType.UINT_16] * 3, unit=self.__modbus_id
                       )]

            currents = [(65535 - value) / 10
                        for value in self.__tcp_client.read_input_registers(
                            206, [ModbusDataType.UINT_16] * 3, unit=self.__modbus_id
                       )]

            power_factors = [value / 100
                            for value in self.__tcp_client.read_input_registers(
                                197, [ModbusDataType.UINT_16] * 3, unit=self.__modbus_id
                            )]

            powers = [-value for value in self.__tcp_client.read_input_registers(
                        130, [ModbusDataType.INT_32] * 3, wordorder=Endian.Little, unit=self.__modbus_id
                     )]
            
            exported, imported = [value * 10
                                  for value in self.__tcp_client.read_input_registers(
                                      72, [ModbusDataType.UINT_32] * 2, wordorder=Endian.Little, unit=self.__modbus_id
                                  )]

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            powers=powers,
            frequency=frequency,
            voltages=voltages,
            currents=currents,
            power_factors=power_factors
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SolaxGen5CounterSetup)
