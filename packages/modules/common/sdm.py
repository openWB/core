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
            self.serial_number = str(self.client.read_holding_registers(0xFC00, ModbusDataType.UINT_32, device_id=self.id))

    def get_imported(self) -> float:
        # smarthome legacy
        time.sleep(0.1)
        return self.client.read_input_registers(0x0048, ModbusDataType.FLOAT_32, device_id=self.id) * 1000


class SdmRegister(IntEnum):
    VOLTAGE_L1 = 0x00
    CURRENT_L1 = 0x06
    POWER_L1 = 0x0C
    POWER_FACTOR_L1 = 0x1E
    FREQUENCY = 0x46
    IMPORTED = 0x48
    EXPORTED = 0x4A


class Sdm630_72(Sdm):
    REG_MAPPING_BULK_1 = (
        (SdmRegister.VOLTAGE_L1, [ModbusDataType.FLOAT_32]*3),
        (SdmRegister.CURRENT_L1, [ModbusDataType.FLOAT_32]*3),
        (SdmRegister.POWER_L1, [ModbusDataType.FLOAT_32]*3),
        (SdmRegister.POWER_FACTOR_L1, [ModbusDataType.FLOAT_32]*3)
    )
    REG_MAPPING_BULK_2 = (
        (SdmRegister.FREQUENCY, ModbusDataType.FLOAT_32),
        (SdmRegister.IMPORTED, ModbusDataType.FLOAT_32),
        (SdmRegister.EXPORTED, ModbusDataType.FLOAT_32),
    )

    def __init__(self, modbus_id: int, client: modbus.ModbusTcpClient_, fault_state: FaultState) -> None:
        super().__init__(modbus_id, client)
        self.fault_state = fault_state

    def get_power(self) -> Tuple[List[float], float]:
        # smarthome legacy
        time.sleep(0.1)
        powers = self.client.read_input_registers(0x0C, [ModbusDataType.FLOAT_32]*3, device_id=self.id)
        power = sum(powers)
        return powers, power

    def get_counter_state(self) -> CounterState:
        # entgegen der Doku können nicht bei allen SDM72 80 Register auf einmal gelesen werden,
        # manche können auch nur 50
        bulk_1 = self.client.read_input_registers_bulk(
            SdmRegister.VOLTAGE_L1, 38, mapping=self.REG_MAPPING_BULK_1, device_id=self.id)
        time.sleep(0.1)
        bulk_2 = self.client.read_input_registers_bulk(
            SdmRegister.FREQUENCY, 8, mapping=self.REG_MAPPING_BULK_2, device_id=self.id)
        resp = {**bulk_1, **bulk_2}
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
            serial_number=self.serial_number
        )
        check_meter_values(counter_state, self.fault_state)
        return counter_state


class Sdm120(Sdm):
    REG_MAPPING_BULK_1 = (
        (SdmRegister.VOLTAGE_L1, ModbusDataType.FLOAT_32),
        (SdmRegister.CURRENT_L1, ModbusDataType.FLOAT_32),
        (SdmRegister.POWER_L1, ModbusDataType.FLOAT_32),
        (SdmRegister.POWER_FACTOR_L1, ModbusDataType.FLOAT_32)
    )
    REG_MAPPING_BULK_2 = (
        (SdmRegister.FREQUENCY, ModbusDataType.FLOAT_32),
        (SdmRegister.IMPORTED, ModbusDataType.FLOAT_32),
        (SdmRegister.EXPORTED, ModbusDataType.FLOAT_32),
    )

    def __init__(self, modbus_id: int, client: modbus.ModbusTcpClient_, fault_state: FaultState) -> None:
        super().__init__(modbus_id, client)
        self.fault_state = fault_state

    def get_power(self) -> Tuple[List[float], float]:
        # smarthome legacy
        time.sleep(0.1)
        power = self.client.read_input_registers(0x0C, ModbusDataType.FLOAT_32, device_id=self.id)
        return [power, 0, 0], power

    def get_counter_state(self) -> CounterState:
        # beim SDM120 steht nichts von Bulk-Reads in der Doku, daher auch auf 50 Register limitiert
        bulk_1 = self.client.read_input_registers_bulk(
            SdmRegister.VOLTAGE_L1, 32, mapping=self.REG_MAPPING_BULK_1, device_id=self.id)
        time.sleep(0.1)
        bulk_2 = self.client.read_input_registers_bulk(
            SdmRegister.FREQUENCY, 8, mapping=self.REG_MAPPING_BULK_2, device_id=self.id)
        resp = {**bulk_1, **bulk_2}
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
            serial_number=self.serial_number
        )
        check_meter_values(counter_state, self.fault_state)
        return counter_state
