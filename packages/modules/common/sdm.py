#!/usr/bin/env python3
import time
from typing import List, Tuple, Optional

from modules.common import modbus
from modules.common.abstract_counter import AbstractCounter
from modules.common.modbus import ModbusDataType


class Sdm(AbstractCounter):
    def __init__(self, modbus_id: int, client: modbus.ModbusTcpClient_) -> None:
        self.client = client
        self.id = modbus_id
        self.last_query = self._get_time_ms()
        self.WAIT_MS_BETWEEN_QUERIES = 100

    def get_imported(self) -> float:
        self._ensure_min_time_between_queries()
        return self.client.read_input_registers(0x0048, ModbusDataType.FLOAT_32, unit=self.id) * 1000

    def get_exported(self) -> float:
        self._ensure_min_time_between_queries()
        return self.client.read_input_registers(0x004a, ModbusDataType.FLOAT_32, unit=self.id) * 1000

    def get_frequency(self) -> float:
        self._ensure_min_time_between_queries()
        frequency = self.client.read_input_registers(0x46, ModbusDataType.FLOAT_32, unit=self.id)
        if frequency > 100:
            frequency = frequency / 10
        return frequency

    def get_serial_number(self) -> Optional[str]:
        self._ensure_min_time_between_queries()
        return str(self.client.read_holding_registers(0xFC00, ModbusDataType.INT_32, unit=self.id))

    # These meters require some minimum time between subsequent Modbus reads. Some Eastron papers recommend 100 ms.
    # Sometimes the time between calls to the get_* methods are much shorter so we forcibly wait for the remaining time.
    def _ensure_min_time_between_queries(self) -> None:
        current_time = self._get_time_ms()
        elapsed_time = current_time - self.last_query
        if elapsed_time < self.WAIT_MS_BETWEEN_QUERIES:
            time.sleep((self.WAIT_MS_BETWEEN_QUERIES - elapsed_time) / 1e3)
        self.last_query = current_time

    def _get_time_ms(self) -> float:
        return time.time_ns() / 1e6


class Sdm630_72(Sdm):
    def __init__(self, modbus_id: int, client: modbus.ModbusTcpClient_) -> None:
        super().__init__(modbus_id, client)

    def get_currents(self) -> List[float]:
        self._ensure_min_time_between_queries()
        return self.client.read_input_registers(0x06, [ModbusDataType.FLOAT_32]*3, unit=self.id)

    def get_power_factors(self) -> List[float]:
        self._ensure_min_time_between_queries()
        return self.client.read_input_registers(0x1E, [ModbusDataType.FLOAT_32]*3, unit=self.id)

    def get_power(self) -> Tuple[List[float], float]:
        self._ensure_min_time_between_queries()
        powers = self.client.read_input_registers(0x0C, [ModbusDataType.FLOAT_32]*3, unit=self.id)
        power = sum(powers)
        return powers, power

    def get_voltages(self) -> List[float]:
        self._ensure_min_time_between_queries()
        return self.client.read_input_registers(0x00, [ModbusDataType.FLOAT_32]*3, unit=self.id)


class Sdm120(Sdm):
    def __init__(self, modbus_id: int, client: modbus.ModbusTcpClient_) -> None:
        super().__init__(modbus_id, client)

    def get_power(self) -> Tuple[List[float], float]:
        self._ensure_min_time_between_queries()
        power = self.client.read_input_registers(0x0C, ModbusDataType.FLOAT_32, unit=self.id)
        return [power, 0, 0], power

    def get_currents(self) -> List[float]:
        self._ensure_min_time_between_queries()
        return [self.client.read_input_registers(0x06, ModbusDataType.FLOAT_32, unit=self.id), 0.0, 0.0]

    def get_voltages(self) -> List[float]:
        self._ensure_min_time_between_queries()
        voltage = self.client.read_input_registers(0x00, ModbusDataType.FLOAT_32, unit=self.id)
        return [voltage, 0.0, 0.0]

    def get_power_factors(self) -> List[float]:
        self._ensure_min_time_between_queries()
        return [self.client.read_input_registers(0x1E, ModbusDataType.FLOAT_32, unit=self.id), 0.0, 0.0]
