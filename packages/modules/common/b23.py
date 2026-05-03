#!/usr/bin/env python3
import time
from typing import List, Optional, Tuple, Union

from modules.common import modbus
from modules.common.abstract_counter import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.fault_state import FaultState
from modules.common.hardware_check import check_meter_values
from modules.common.modbus import ModbusDataType


class B23(AbstractCounter):
    """Class for reading data from ABB B23 energy counter via Modbus TCP.
    Register definitions are based on ABB B23 Modbus register map.
    https://search.abb.com/library/Download.aspx?DocumentID=2CMC485003M0201
    """

    """NaN values for all data types.
    """
    NAN = {
        "UINT_16": 0xFFFF,
        "INT_16": 0x7FFF,
        "UINT_32": 0xFFFFFFFF,
        "INT_32": 0x7FFFFFFF,
        "UINT_64": 0xFFFFFFFFFFFFFFFF,
        "INT_64": 0x7FFFFFFFFFFFFFFF,
    }

    def __init__(self, modbus_id: int, client: modbus.ModbusTcpClient_, fault_state: FaultState) -> None:
        self.client = client
        self.id = modbus_id
        self.fault_state = fault_state

    def check_nan(self, raw_value: int, value: any, data_type: ModbusDataType) -> Optional[Union[float, int]]:
        """Checks if the value is a NaN and returns None if it is.
        """
        if raw_value == self.NAN[data_type.name]:
            return None
        return value

    def get_serial_number(self) -> str:
        """Returns serial number of the device.
        """
        # firmware version: 0x8908, 8 Registers, ASCII
        # Modbus mapping version: 0x8910, 1 Register, only 2 bytes
        data_type = ModbusDataType.UINT_32
        time.sleep(0.1)
        value = self.client.read_holding_registers(0x8900, data_type, device_id=self.id)
        return str(self.check_nan(value, value, data_type))

    def get_currents(self) -> List[float]:
        """Returns currents for all 3 phases in A.
        """
        data_type = ModbusDataType.UINT_32
        time.sleep(0.1)
        return [self.check_nan(val, val / 100, data_type)
                for val in self.client.read_holding_registers(0x5B0C, [data_type]*3, device_id=self.id)]

    def get_frequency(self) -> float:
        """Returns frequency in Hz.
        """
        data_type = ModbusDataType.UINT_16
        time.sleep(0.1)
        raw_value = self.client.read_holding_registers(0x5B2C, data_type, device_id=self.id)
        return self.check_nan(raw_value, raw_value / 100, data_type)

    def get_imported(self) -> float:
        """Returns imported energy in Wh.
        """
        data_type = ModbusDataType.UINT_64
        time.sleep(0.1)
        raw_value = self.client.read_holding_registers(0x5000, data_type, device_id=self.id)
        return self.check_nan(raw_value, raw_value * 10, data_type)

    def get_exported(self) -> float:
        time.sleep(0.1)
        return self.client.read_holding_registers(0x5004, ModbusDataType.UINT_64, device_id=self.id) * 10

    def get_power(self) -> Tuple[List[float], float]:
        """Returns power per phase and total power.
        """
        data_type = ModbusDataType.INT_32
        time.sleep(0.1)
        # reading of total power and power per phase in one call
        powers = [self.check_nan(val, val / 100, data_type)
                  for val in self.client.read_holding_registers(0x5B14, [data_type]*4, device_id=self.id)]
        return powers[1:4], powers[0]

    def get_power_factors(self) -> List[float]:
        """Returns power factors for all 3 phases.
        Documented registers are 0x5B3B, 0x5B3D, 0x5B3F but they are not available in all devices.
        Alternative registers for "DMTME multimeters" (0x1018, 0x101A, 0x101C; INT_32) also not available.
        """
        data_type = ModbusDataType.INT_16
        time.sleep(0.1)
        return [self.check_nan(val, val / 1000, data_type)
                for val in self.client.read_holding_registers(0x5B3B, [data_type]*3, device_id=self.id)]

    def get_voltages(self) -> List[float]:
        """Returns voltages for all 3 phases.
        """
        data_type = ModbusDataType.UINT_32
        time.sleep(0.1)
        values = [self.check_nan(val, val / 10, data_type)
                  for val in self.client.read_holding_registers(0x5B00, [data_type]*3, device_id=self.id)]
        return values

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
