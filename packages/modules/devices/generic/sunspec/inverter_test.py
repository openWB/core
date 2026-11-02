import struct
from typing import Dict, Union
from unittest.mock import Mock

import pytest

from modules.common.modbus import ModbusDataType
from modules.common.sunspec.discovery import SUNS_MARKER, SunSpecDiscoveryError
from modules.devices.generic.sunspec.config import SunspecInverterSetup
from modules.devices.generic.sunspec.inverter import SunspecInverter


class FakeSunSpecClient:
    def __init__(self, registers: Dict[int, int]):
        self.registers = registers

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read_holding_registers(self, address: int, types: Union[ModbusDataType, list], unit: int = 1):
        single = isinstance(types, ModbusDataType)
        type_list = [types] if single else types
        result = []
        for t in type_list:
            if t == ModbusDataType.UINT_32:
                high, low = self.registers[address], self.registers[address + 1]
                result.append((high << 16) | low)
                address += 2
            elif t == ModbusDataType.FLOAT_32:
                high, low = self.registers[address], self.registers[address + 1]
                result.append(struct.unpack(">f", struct.pack(">HH", high, low))[0])
                address += 2
            else:
                value = self.registers.get(address, 0)
                if t == ModbusDataType.INT_16 and value >= 0x8000:
                    value -= 0x10000
                result.append(value)
                address += 1
        return result[0] if single else result


def _registers_with_float_inverter(base: int, w: float, wh: float) -> Dict[int, int]:
    registers = {base: SUNS_MARKER >> 16, base + 1: SUNS_MARKER & 0xFFFF}
    registers.update({base + 2: 113, base + 3: 60})
    model_base = base + 4
    for offset, value in ((20, w), (30, wh)):
        high, low = struct.unpack(">HH", struct.pack(">f", value))
        registers[model_base + offset], registers[model_base + offset + 1] = high, low
    registers.update({model_base + 60: 0xFFFF, model_base + 61: 0})
    return registers


def _registers_with_int_sf_inverter(base: int, w: int, w_sf: int, wh: int, wh_sf: int) -> Dict[int, int]:
    registers = {base: SUNS_MARKER >> 16, base + 1: SUNS_MARKER & 0xFFFF}
    registers.update({base + 2: 103, base + 3: 50})
    model_base = base + 4
    registers[model_base + 12] = w & 0xFFFF
    registers[model_base + 13] = w_sf & 0xFFFF
    registers[model_base + 22], registers[model_base + 23] = wh >> 16, wh & 0xFFFF
    registers[model_base + 24] = wh_sf & 0xFFFF
    registers.update({model_base + 50: 0xFFFF, model_base + 51: 0})
    return registers


def _inverter(registers: Dict[int, int]) -> SunspecInverter:
    inverter = SunspecInverter(SunspecInverterSetup(), client=FakeSunSpecClient(registers), device_id=1)
    inverter.initialize()
    inverter.peak_filter.check_values = Mock(side_effect=lambda power, imp, exp: (imp, exp))
    inverter.sim_counter.sim_count = Mock(return_value=(0, 0))
    return inverter


def test_reads_power_and_exported_from_float_inverter_model():
    registers = _registers_with_float_inverter(40000, w=-155.9, wh=2205723.8)

    inverter = _inverter(registers)
    inverter.update()

    assert inverter.peak_filter.check_values.call_args[0][0] == pytest.approx(155.9)
    assert inverter.peak_filter.check_values.call_args[0][2] == pytest.approx(2205723.8, abs=0.1)


def test_reads_power_and_exported_from_int_sf_inverter_model():
    registers = _registers_with_int_sf_inverter(40000, w=-1559, w_sf=-1, wh=22057238, wh_sf=-1)

    inverter = _inverter(registers)
    inverter.update()

    assert inverter.peak_filter.check_values.call_args[0][0] == pytest.approx(155.9)
    assert inverter.peak_filter.check_values.call_args[0][2] == pytest.approx(2205723.8, abs=0.1)


def test_raises_clear_error_if_no_known_inverter_model_is_found():
    registers = {40000: SUNS_MARKER >> 16, 40001: SUNS_MARKER & 0xFFFF, 40002: 1, 40003: 2, 40006: 0xFFFF, 40007: 0}

    with pytest.raises(SunSpecDiscoveryError, match="SunSpec Wechselrichter"):
        _inverter(registers)
