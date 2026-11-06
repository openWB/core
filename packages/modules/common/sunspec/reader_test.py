import struct
from typing import Dict

import pytest

from modules.common.modbus import ModbusDataType
from modules.common.sunspec.discovery import SunSpecModelLocation
from modules.common.sunspec.points import Point
from modules.common.sunspec.reader import read_point


class FakeSunSpecClient:
    def __init__(self, registers: Dict[int, int]):
        self.registers = registers

    def read_holding_registers(self, address: int, data_type: ModbusDataType, unit: int = 1):
        if data_type == ModbusDataType.FLOAT_32:
            high, low = self.registers[address], self.registers[address + 1]
            return struct.unpack(">f", struct.pack(">HH", high, low))[0]
        if data_type == ModbusDataType.UINT_32:
            return (self.registers[address] << 16) | self.registers[address + 1]
        value = self.registers[address]
        if data_type == ModbusDataType.INT_16 and value >= 0x8000:
            value -= 0x10000
        return value


def _float_registers(address: int, value: float) -> Dict[int, int]:
    high, low = struct.unpack(">HH", struct.pack(">f", value))
    return {address: high, address + 1: low}


def _int_registers(address: int, value: int) -> Dict[int, int]:
    return {address: value & 0xFFFF}


MODEL = SunSpecModelLocation(model_id=113, base_address=40072, length=60)


def test_reads_float32_point():
    registers = _float_registers(40072 + 20, -155.9)
    point = Point(offset=20, type="float32")

    assert read_point(FakeSunSpecClient(registers), MODEL, point) == pytest.approx(-155.9)


def test_float32_nan_is_not_implemented():
    registers = _float_registers(40072 + 20, float("nan"))
    point = Point(offset=20, type="float32")

    assert read_point(FakeSunSpecClient(registers), MODEL, point) is None


def test_reads_int16_point_scaled_by_sf():
    registers = {}
    registers.update(_int_registers(40072 + 12, -1559))
    registers.update(_int_registers(40072 + 13, -1))  # W_SF = -1 -> *0.1
    point = Point(offset=12, type="int16", sf_offset=13)

    assert read_point(FakeSunSpecClient(registers), MODEL, point) == pytest.approx(-155.9)


def test_int16_not_implemented_sentinel_is_none():
    registers = _int_registers(40072 + 12, -32768)
    point = Point(offset=12, type="int16", sf_offset=13)

    assert read_point(FakeSunSpecClient(registers), MODEL, point) is None


def test_reads_uint16_point_scaled_by_sf():
    registers = {}
    registers.update(_int_registers(40072 + 4, 1234))
    registers.update(_int_registers(40072 + 11, -1))  # V_SF = -1 -> *0.1
    point = Point(offset=4, type="uint16", sf_offset=11)

    assert read_point(FakeSunSpecClient(registers), MODEL, point) == pytest.approx(123.4)


def test_uint16_not_implemented_sentinel_is_none():
    registers = _int_registers(40072 + 4, 0xFFFF)
    point = Point(offset=4, type="uint16", sf_offset=11)

    assert read_point(FakeSunSpecClient(registers), MODEL, point) is None


def test_reads_acc32_point_scaled_by_sf():
    registers = {}
    registers[40072 + 22], registers[40072 + 23] = 0, 22057238
    registers.update(_int_registers(40072 + 24, -2))  # WH_SF = -2 -> *0.01
    point = Point(offset=22, type="acc32", sf_offset=24)

    assert read_point(FakeSunSpecClient(registers), MODEL, point) == pytest.approx(220572.38)
