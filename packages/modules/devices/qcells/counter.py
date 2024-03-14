#!/usr/bin/env python3
from typing import Dict, Union
from pymodbus.constants import Endian

from dataclass_utils import dataclass_from_dict
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_counter_value_store
from modules.devices.qcells.config import QCellsCounterSetup


class QCellsCounter:
    def __init__(self,
                 component_config: Union[Dict, QCellsCounterSetup],
                 modbus_id: int) -> None:
        self.component_config = dataclass_from_dict(QCellsCounterSetup, component_config)
        self.__modbus_id = modbus_id
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, client: ModbusTcpClient_):
        power = client.read_input_registers(0x0046, ModbusDataType.INT_32, wordorder=Endian.Little,
                                            unit=self.__modbus_id) * -1
        frequency = client.read_input_registers(
            0x0007, ModbusDataType.UINT_16, unit=self.__modbus_id) / 100
        try:
            powers = [-value for value in client.read_input_registers(
                0x0082, [ModbusDataType.INT_32] * 3, wordorder=Endian.Little, unit=self.__modbus_id
            )]
        except Exception:
            powers = None
        try:
            voltages = [client.read_input_registers(
                0x006A, ModbusDataType.UINT_16, unit=self.__modbus_id
            ) / 10, client.read_input_registers(
                0x006E, ModbusDataType.UINT_16, unit=self.__modbus_id
            ) / 10, client.read_input_registers(
                0x0072, ModbusDataType.UINT_16, unit=self.__modbus_id
            ) / 10]
            if voltages[0] < 1:
                voltages[0] = 230
            if voltages[1] < 1:
                voltages[1] = 230
            if voltages[2] < 1:
                voltages[2] = 230
        except Exception:
            voltages = [230, 230, 230]
        exported, imported = [value * 10
                              for value in client.read_input_registers(
                                  0x0048, [ModbusDataType.UINT_32] * 2,
                                  wordorder=Endian.Little, unit=self.__modbus_id
                              )]

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            powers=powers,
            frequency=frequency,
            voltages=voltages,
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=QCellsCounterSetup)
