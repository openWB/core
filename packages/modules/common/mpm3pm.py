#!/usr/bin/env python3
from typing import List, Tuple

from modules.common import modbus
from modules.common.abstract_counter import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.modbus import ModbusDataType


class Mpm3pm(AbstractCounter):
    def __init__(self, modbus_id: int, client: modbus.ModbusTcpClient_) -> None:
        self.client = client
        self.id = modbus_id

    def get_voltages(self) -> List[float]:
        return [val / 10 for val in self.client.read_input_registers(
            0x08, [ModbusDataType.UINT_32]*3, unit=self.id)]

    def get_imported(self) -> float:
        # Faktorisierung anders als in der Dokumentation angegeben
        return self.client.read_input_registers(0x0002, ModbusDataType.UINT_32, unit=self.id) * 10

    def get_power(self) -> Tuple[List[float], float]:
        powers = [val / 100 for val in self.client.read_input_registers(
            0x14, [ModbusDataType.INT_32]*3, unit=self.id)]
        power = self.client.read_input_registers(0x26, ModbusDataType.INT_32, unit=self.id) / 100
        return powers, power

    def get_exported(self) -> float:
        # Faktorisierung anders als in der Dokumentation angegeben
        return self.client.read_input_registers(0x0004, ModbusDataType.UINT_32, unit=self.id) * 10

    def get_power_factors(self) -> List[float]:
        # Faktorisierung anders als in der Dokumentation angegeben?
        factors = [val / 10 for val in self.client.read_input_registers(
            0x20, [ModbusDataType.UINT_32]*3, unit=self.id)]
        # check if the absolute value of an entry in factors is greater 1
        if any([abs(factor) > 1 for factor in factors]):
            factors = [factor / 100 for factor in factors]
        return factors

    def get_frequency(self) -> float:
        return self.client.read_input_registers(0x2c, ModbusDataType.UINT_32, unit=self.id) / 100

    def get_currents(self) -> List[float]:
        return [val / 100 for val in self.client.read_input_registers(
            0x0E, [ModbusDataType.UINT_32]*3, unit=self.id)]

    def get_serial_number(self) -> str:
        return str(self.client.read_input_registers(0x33, ModbusDataType.UINT_32, unit=self.id))

    def get_counter_state(self) -> CounterState:
        powers, power = self.get_power()
        return CounterState(
            voltages=self.get_voltages(),
            currents=self.get_currents(),
            powers=powers,
            power=power,
            power_factors=self.get_power_factors(),
            imported=self.get_imported(),
            exported=self.get_exported(),
            frequency=self.get_frequency(),
            serial_number=self.get_serial_number()
        )
