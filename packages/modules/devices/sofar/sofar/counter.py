#!/usr/bin/env python3
from typing import Any, TypedDict

from modules.devices.sofar.sofar.config import SofarCounterSetup
from modules.common.store import get_counter_value_store
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.component_type import ComponentDescriptor
from modules.common.component_state import CounterState
from modules.common.abstract_device import AbstractCounter


class KwargsDict(TypedDict):
    client: ModbusTcpClient_
    modbus_id: int


class SofarCounter(AbstractCounter):
    def __init__(self, component_config: SofarCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        # 0x0485 ActivePower_output_total Int16 in kW accuracy 0,01 discharge + charge -
        # 0x0488 ActivePower_PCC_total Int16 0,01 kW
        power = self.client.read_holding_registers(0x0488, ModbusDataType.INT_16, device_id=self.__modbus_id) * -10
        # 0x0484 Frequency_Grid UInt16 in Hz accuracy 0,01
        frequency = self.client.read_holding_registers(
            0x0484, ModbusDataType.UINT_16, device_id=self.__modbus_id) / 100
        try:
            powers = [
                self.client.read_holding_registers(0x0493, ModbusDataType.INT_16, device_id=self.__modbus_id) * -10,
                self.client.read_holding_registers(0x049E, ModbusDataType.INT_16, device_id=self.__modbus_id) * -10,
                self.client.read_holding_registers(0x04A9, ModbusDataType.INT_16, device_id=self.__modbus_id) * -10]
        except Exception:
            powers = None
        # 0x0692 Energy_Selling_Total UInt32 in kwH accuracy 0,01 LSB
        # 0x0693 Energy_Selling_Total UInt32 in kwH accuracy 0,01
        exported = self.client.read_holding_registers(0x0692, ModbusDataType.UINT_32, device_id=self.__modbus_id) * 100
        # 0x068E Energy_Purchase_Total UInt32 in kwH accuracy 0,01 LSB
        # 0x068F Energy_Purchase_Total UInt32 in kwH accuracy 0,01
        imported = self.client.read_holding_registers(0x068E, ModbusDataType.UINT_32, device_id=self.__modbus_id) * 100

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            powers=powers,
            frequency=frequency
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SofarCounterSetup)
