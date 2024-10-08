#!/usr/bin/env python3
from typing import Dict, Union
from pymodbus.constants import Endian

from dataclass_utils import dataclass_from_dict
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_counter_value_store
from modules.devices.sofar.sofar.config import SofarCounterSetup


class SofarCounter:
    def __init__(self,
                 component_config: Union[Dict, SofarCounterSetup],
                 modbus_id: int) -> None:
        self.component_config = dataclass_from_dict(SofarCounterSetup, component_config)
        self.__modbus_id = modbus_id
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, client: ModbusTcpClient_):
        # 0x0485 ActivePower_output_total Int16 in kW accuracy 0,01 discharge + charge -
        # 0x0488 ActivePower_PCC_total Int16 0,01 kW
        power = client.read_input_registers(0x0488, ModbusDataType.INT_16, wordorder=Endian.Little,
                                            unit=self.__modbus_id) * -1
        # 0x0484 Frequency_Grid UInt16 in Hz accuracy 0,01
        frequency = client.read_input_registers(
            0x0484, ModbusDataType.UINT_16, unit=self.__modbus_id) / 100
        try:
            # 0x048F ActivePower_Output_R UInt16 in V accuracy 0,1
            # 0x0493 ActivePower_PCC_R Int16 in kW accuracy 0,01
            powers = [-value for value in client.read_input_registers(
                0x0493, [ModbusDataType.INT_16] * 1, wordorder=Endian.Little, unit=self.__modbus_id
            )]
        except Exception:
            powers = None
        try:
            voltages = [client.read_input_registers(
                # 048D Voltage_Phase_R UInt16 in V accuracy 0,1
                0x048D, ModbusDataType.UINT_16, unit=self.__modbus_id
            ) / 10, client.read_input_registers(
                # 0498 Voltage_Phase_S UInt16 in V accuracy 0,1
                0x0498, ModbusDataType.UINT_16, unit=self.__modbus_id
            ) / 10, client.read_input_registers(
                # 04A3 Voltage_Phase_T UInt16 in V accuracy 0,1
                0x04A3, ModbusDataType.UINT_16, unit=self.__modbus_id
            ) / 10]
            if voltages[0] < 1:
                voltages[0] = 230
            if voltages[1] < 1:
                voltages[1] = 230
            if voltages[2] < 1:
                voltages[2] = 230
        except Exception:
            voltages = [230, 230, 230]
        exported = [value * 10
                    for value in client.read_input_registers(
                        # 0x0692 Energy_Selling_Total UInt32 in kwH accuracy 0,01 LSB
                        # 0x0693 Energy_Selling_Total UInt32 in kwH accuracy 0,01
                        0x0692, [ModbusDataType.UINT_32] * 10,
                        wordorder=Endian.Little, unit=self.__modbus_id)]
        imported = [value * 10
                    for value in client.read_input_registers(
                        # 0x068E Energy_Purchase_Total UInt32 in kwH accuracy 0,01 LSB
                        # 0x068F Energy_Purchase_Total UInt32 in kwH accuracy 0,01
                        0x068E, [ModbusDataType.UINT_32] * 10,
                        wordorder=Endian.Little, unit=self.__modbus_id)]

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            powers=powers,
            frequency=frequency,
            voltages=voltages,
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SofarCounterSetup)
