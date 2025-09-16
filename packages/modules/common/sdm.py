#!/usr/bin/env python3
from enum import IntEnum

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
    CURRENT_L1 = 0x06
    POWER_L1 = 0x0C
    POWER_FACTOR_L1 = 0x1E
    FREQUENCY = 0x46
    IMPORTED = 0x48
    EXPORTED = 0x4A


class Sdm630_72(Sdm):
    REG_MAPPING = (
        (SdmRegister.VOLTAGE_L1, [ModbusDataType.FLOAT_32]*3),
        (SdmRegister.CURRENT_L1, [ModbusDataType.FLOAT_32]*3),
        (SdmRegister.POWER_L1, [ModbusDataType.FLOAT_32]*3),
        (SdmRegister.POWER_FACTOR_L1, [ModbusDataType.FLOAT_32]*3),
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
            power=sum(resp[SdmRegister.POWER_L1]),
            voltages=resp[SdmRegister.VOLTAGE_L1],
            currents=resp[SdmRegister.CURRENT_L1],
            powers=resp[SdmRegister.POWER_L1],
            power_factors=resp[SdmRegister.POWER_FACTOR_L1],
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
