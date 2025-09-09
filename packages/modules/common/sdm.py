#!/usr/bin/env python3
from enum import IntEnum
import time
from typing import List, Tuple

from modules.common import modbus
from modules.common.abstract_counter import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.fault_state import FaultState
from modules.common.hardware_check import check_meter_values
from modules.common.modbus import ModbusDataType


class Sdm(AbstractCounter):
    def __init__(self, modbus_id: int, client: modbus.ModbusTcpClient_) -> None:
        self.client = client
        self.id = modbus_id
        with client:
            self.serial_number = str(self.client.read_holding_registers(0xFC00, ModbusDataType.UINT_32, unit=self.id))


class SdmRegister(IntEnum):
    VOLTAGE_L1 = 0x00
    VOLTAGE_L2 = 0x02
    VOLTAGE_L3 = 0x04
    CURRENT_L1 = 0x06
    CURRENT_L2 = 0x08
    CURRENT_L3 = 0x0A
    POWER_L1 = 0x0C
    POWER_L2 = 0x0E
    POWER_L3 = 0x10
    POWER_FACTOR_L1 = 0x1E
    POWER_FACTOR_L2 = 0x20
    POWER_FACTOR_L3 = 0x22
    FREQUENCY = 0x46
    IMPORTED = 0x48
    EXPORTED = 0x4A


class Sdm630_72(Sdm):
    REG_MAPPING = (
        (SdmRegister.VOLTAGE_L1, ModbusDataType.FLOAT_32),
        (SdmRegister.VOLTAGE_L2, ModbusDataType.FLOAT_32),
        (SdmRegister.VOLTAGE_L3, ModbusDataType.FLOAT_32),
        (SdmRegister.CURRENT_L1, ModbusDataType.FLOAT_32),
        (SdmRegister.CURRENT_L2, ModbusDataType.FLOAT_32),
        (SdmRegister.CURRENT_L3, ModbusDataType.FLOAT_32),
        (SdmRegister.POWER_L1, ModbusDataType.FLOAT_32),
        (SdmRegister.POWER_L2, ModbusDataType.FLOAT_32),
        (SdmRegister.POWER_L3, ModbusDataType.FLOAT_32),
        (SdmRegister.POWER_FACTOR_L1, ModbusDataType.FLOAT_32),
        (SdmRegister.POWER_FACTOR_L2, ModbusDataType.FLOAT_32),
        (SdmRegister.POWER_FACTOR_L3, ModbusDataType.FLOAT_32),
        (SdmRegister.FREQUENCY, ModbusDataType.FLOAT_32),
        (SdmRegister.IMPORTED, ModbusDataType.FLOAT_32),
        (SdmRegister.EXPORTED, ModbusDataType.FLOAT_32),
    )

    def __init__(self, modbus_id: int, client: modbus.ModbusTcpClient_, fault_state: FaultState) -> None:
        super().__init__(modbus_id, client)
        self.fault_state = fault_state

    def get_counter_state(self) -> CounterState:
        resp = self.client.read_input_registers_bulk(
            SdmRegister.VOLTAGE_L1, 76, mapping=self.REG_MAPPING, unit=self.id)
        frequency = resp[SdmRegister.FREQUENCY]
        if frequency > 100:
            frequency = frequency / 10
        counter_state = CounterState(
            imported=resp[SdmRegister.IMPORTED]*1000,
            exported=resp[SdmRegister.EXPORTED]*1000,
            power=sum(resp[r] for r in (SdmRegister.POWER_L1, SdmRegister.POWER_L2, SdmRegister.POWER_L3)),
            voltages=[resp[r]
                      for r in (SdmRegister.VOLTAGE_L1, SdmRegister.VOLTAGE_L2, SdmRegister.VOLTAGE_L3)],
            currents=[resp[r]
                      for r in (SdmRegister.CURRENT_L1, SdmRegister.CURRENT_L2, SdmRegister.CURRENT_L3)],
            powers=[resp[r] for r in (SdmRegister.POWER_L1, SdmRegister.POWER_L2, SdmRegister.POWER_L3)],
            power_factors=[resp[r] for r in (SdmRegister.POWER_FACTOR_L1,
                                             SdmRegister.POWER_FACTOR_L2, SdmRegister.POWER_FACTOR_L3)],
            frequency=frequency,
            serial_number=self.get_serial_number()
        )
        check_meter_values(counter_state, self.fault_state)
        return counter_state


class Sdm120(Sdm):
    REG_MAPPING = (
        (SdmRegister.VOLTAGE_L1, ModbusDataType.FLOAT_32),
        (SdmRegister.CURRENT_L1, ModbusDataType.FLOAT_32),
        (SdmRegister.POWER_L1, ModbusDataType.FLOAT_32),
        (SdmRegister.POWER_FACTOR_L1, ModbusDataType.FLOAT_32),
        (SdmRegister.FREQUENCY, ModbusDataType.FLOAT_32),
        (SdmRegister.IMPORTED, ModbusDataType.FLOAT_32),
        (SdmRegister.EXPORTED, ModbusDataType.FLOAT_32),
    )

    def __init__(self, modbus_id: int, client: modbus.ModbusTcpClient_, fault_state: FaultState) -> None:
        super().__init__(modbus_id, client)
        self.fault_state = fault_state

    def get_counter_state(self) -> CounterState:
        resp = self.client.read_input_registers_bulk(
            SdmRegister.VOLTAGE_L1, 76, mapping=self.REG_MAPPING, unit=self.id)
        frequency = resp[SdmRegister.FREQUENCY]
        if frequency > 100:
            frequency = frequency / 10
        counter_state = CounterState(
            imported=resp[SdmRegister.IMPORTED]*1000,
            exported=resp[SdmRegister.EXPORTED]*1000,
            power=resp[SdmRegister.POWER_L1],
            voltages=[resp[SdmRegister.VOLTAGE_L1], 0, 0],
            currents=[resp[SdmRegister.CURRENT_L1], 0, 0],
            powers=[resp[SdmRegister.POWER_L1], 0, 0],
            power_factors=[resp[SdmRegister.POWER_FACTOR_L1], 0, 0],
            frequency=frequency,
            serial_number=self.get_serial_number()
        )
        check_meter_values(counter_state, self.fault_state)
        return counter_state
