#!/usr/bin/env python3
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

    def get_imported(self) -> float:
        return self.client.read_input_registers(0x0048, ModbusDataType.FLOAT_32, unit=self.id) * 1000

    def get_exported(self) -> float:
        return self.client.read_input_registers(0x004a, ModbusDataType.FLOAT_32, unit=self.id) * 1000

    def get_frequency(self) -> float:
        frequency = self.client.read_input_registers(0x46, ModbusDataType.FLOAT_32, unit=self.id)
        if frequency > 100:
            frequency = frequency / 10
        return frequency

    def get_serial_number(self) -> str:
        return self.serial_number


class Sdm630_72(Sdm):
    def __init__(self, modbus_id: int, client: modbus.ModbusTcpClient_, fault_state: FaultState) -> None:
        super().__init__(modbus_id, client)
        self.fault_state = fault_state

    def get_currents(self) -> List[float]:
        return self.client.read_input_registers(0x06, [ModbusDataType.FLOAT_32]*3, unit=self.id)

    def get_power_factors(self) -> List[float]:
        return self.client.read_input_registers(0x1E, [ModbusDataType.FLOAT_32]*3, unit=self.id)

    def get_power(self) -> Tuple[List[float], float]:
        powers = self.client.read_input_registers(0x0C, [ModbusDataType.FLOAT_32]*3, unit=self.id)
        power = sum(powers)
        return powers, power

    def get_voltages(self) -> List[float]:
        return self.client.read_input_registers(0x00, [ModbusDataType.FLOAT_32]*3, unit=self.id)

    def get_counter_state(self) -> CounterState:
        powers, power = self.get_power()
        counter_state = CounterState(
            imported=self.get_imported(),
            exported=self.get_exported(),
            power=power,
            voltages=self.get_voltages(),
            currents=self.get_currents(),
            powers=powers,
            power_factors=self.get_power_factors(),
            frequency=self.get_frequency(),
            serial_number=self.get_serial_number()
        )
        check_meter_values(counter_state, self.fault_state)
        return counter_state


class Sdm120(Sdm):
    def __init__(self, modbus_id: int, client: modbus.ModbusTcpClient_, fault_state: FaultState) -> None:
        super().__init__(modbus_id, client)
        self.fault_state = fault_state

    def get_power(self) -> Tuple[List[float], float]:
        power = self.client.read_input_registers(0x0C, ModbusDataType.FLOAT_32, unit=self.id)
        return [power, 0, 0], power

    def get_currents(self) -> List[float]:
        return [self.client.read_input_registers(0x06, ModbusDataType.FLOAT_32, unit=self.id), 0, 0]

    def get_counter_state(self) -> CounterState:
        powers, power = self.get_power()
        counter_state = CounterState(
            imported=self.get_imported(),
            exported=self.get_exported(),
            power=power,
            currents=self.get_currents(),
            powers=powers,
            frequency=self.get_frequency(),
            serial_number=self.get_serial_number()
        )
        check_meter_values(counter_state, self.fault_state)
        return counter_state
