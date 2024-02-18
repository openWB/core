#!/usr/bin/env python3
import time
from typing import List, Tuple

from modules.common import modbus
from modules.common.abstract_counter import AbstractCounter
from modules.common.modbus import ModbusDataType


class B23(AbstractCounter):
    def __init__(self, modbus_id: int, client: modbus.ModbusTcpClient_) -> None:
        self.client = client
        self.id = modbus_id
        self.power_factors_via_modbus_capability: bool = True

    def get_currents(self) -> List[float]:
        time.sleep(0.1)
        return [val / 100 for val in self.client.read_holding_registers(
            0x5B0C, [ModbusDataType.UINT_32]*3, unit=self.id)]

    def get_frequency(self) -> float:
        time.sleep(0.1)
        return self.client.read_holding_registers(0x5B2C, ModbusDataType.UINT_16, unit=self.id) / 100

    def get_imported(self) -> float:
        time.sleep(0.1)
        return self.client.read_holding_registers(0x5000, ModbusDataType.UINT_64, unit=self.id) * 10

    def get_power(self) -> Tuple[List[float], float]:
        time.sleep(0.1)
        # reading of total power and power per phase in one call
        powers = [val / 100 for val in self.client.read_holding_registers(
            0x5B14, [ModbusDataType.INT_32]*4, unit=self.id)]
        return powers[1:4], powers[0]

    def get_power_factors(self) -> List[float]:
        # skipping reading modbus registers, if B23 is not capable of providing valid values on those registers
        if not self.power_factors_via_modbus_capability:
            return [0]*3
        time.sleep(0.1)
        pf = [val / 1000 for val in self.client.read_holding_registers(
            0x5B3B, [ModbusDataType.INT_16]*3, unit=self.id)]
        # checking for capility of providing valid values on power factor registers
        if pf[0] > 1:
            # storing incapability for skipping modbus calls in further loops
            self.power_factors_via_modbus_capability = False
            return [0]*3
        return pf

    def get_voltages(self) -> List[float]:
        time.sleep(0.1)
        return [val / 10 for val in self.client.read_holding_registers(
            0x5B00, [ModbusDataType.UINT_32]*3, unit=self.id)]
