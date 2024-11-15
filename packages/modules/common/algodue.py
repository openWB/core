#!/usr/bin/env python3
import logging
from typing import List, Tuple, Optional

from helpermodules.logger import ModifyLoglevelContext

from modules.common import modbus
from modules.common.abstract_counter import AbstractCounter
from modules.common.modbus import ModbusDataType

log = logging.getLogger(__name__)


class Algodue(AbstractCounter):
    serial_cached: Optional[str] = None
    model_cached: Optional[str] = None

    def __init__(self, modbus_id: int, client: modbus.ModbusTcpClient_) -> None:
        self.client = client
        self.id = modbus_id

    def get_imported(self) -> float:
        return self.client.read_input_registers(0x1106, ModbusDataType.FLOAT_32, unit=self.id)

    def get_exported(self) -> float:
        return self.client.read_input_registers(0x110e, ModbusDataType.FLOAT_32, unit=self.id)

    def get_frequency(self) -> float:
        return self.client.read_input_registers(0x1038, ModbusDataType.FLOAT_32, unit=self.id)

    def get_serial_number(self) -> Optional[str]:
        # serial will never change - at least until power cycle
        if self.serial_cached is None:
            serial_chars = self.client.read_holding_registers(0x500, [ModbusDataType.UINT_8]*10, unit=self.id)
            serial_string = ""
            for x in serial_chars:
                serial_string += chr(x)
            # due to caching this appears rarely - but it's nice to have always have it in main log
            with ModifyLoglevelContext(log, logging.DEBUG):
                log.debug("Algodue meter serial " + serial_string)
            self.serial_cached = serial_string
        return self.serial_cached

    def get_currents(self) -> List[float]:
        return self.client.read_input_registers(0x100E, [ModbusDataType.FLOAT_32]*3, unit=self.id)

    def get_power_factors(self) -> List[float]:
        return self.client.read_input_registers(0x1018, [ModbusDataType.FLOAT_32]*3, unit=self.id)

    def get_power(self) -> Tuple[List[float], float]:
        powers = self.client.read_input_registers(0x1020, [ModbusDataType.FLOAT_32]*3, unit=self.id)
        power = sum(powers)
        return powers, power

    def get_voltages(self) -> List[float]:
        return self.client.read_input_registers(0x1000, [ModbusDataType.FLOAT_32]*3, unit=self.id)

    def get_model(self) -> Optional[str]:
        # model will never change - at least until power cycle
        if self.model_cached is None:
            model_id = self.client.read_holding_registers(0x505, ModbusDataType.UINT_16, unit=self.id)
            model_string = "unknown"
            if model_id == 0x03:
                model_string = "6 A, 3 phases, 4 wires"
            elif model_id == 0x08:
                model_string = "80 A, 3 phases, 4 wires"
            elif model_id == 0x0c:
                model_string = "80 A, 1 phase, 2 wires"
            elif model_id == 0x10:
                model_string = "40 A, 1 phase, 2 wires"
            elif model_id == 0x12:
                model_string = "63 A, 3 phases, 4 wires"

            type_id = self.client.read_holding_registers(0x506, ModbusDataType.UINT_16, unit=self.id)
            type_string = "unknown"
            if type_id == 0x00:
                type_string = "NO MID, RESET"
            elif type_id == 0x01:
                type_string = "MID"
            elif type_id == 0x02:
                type_string = "NO MID"
            elif type_id == 0x03:
                type_string = "NO MID, Wiring selection"
            elif type_id == 0x05:
                type_string = "MID no varh"
            elif type_id == 0x09:
                type_string = "MID Wiring selection"
            elif type_id == 0x0a:
                type_string = "MID no varh, Wiring selection"
            elif type_id == 0x0b:
                type_string = "NO MID, RESET, Wiring selection"
            meterinfo = "Algodue UEM " + model_string + ", " + type_string

            # due to caching this appears rarely - but it's nice to have always have it in main log
            with ModifyLoglevelContext(log, logging.DEBUG):
                log.debug("Algodue model: " + meterinfo)
            self.model_cached = meterinfo
        return self.model_cached
