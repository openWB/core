from typing import Dict, Union
from unittest.mock import Mock

import pytest

from modules.common.modbus import ModbusDataType
from modules.common.sunspec import points
from modules.common.sunspec.discovery import SUNS_MARKER
from modules.devices.generic.sunspec.bat import SunspecBat
from modules.devices.generic.sunspec.config import SunspecBatSetup

BATTERY_BASE = 40000


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
                high, low = self.registers.get(address, 0), self.registers.get(address + 1, 0)
                result.append((high << 16) | low)
                address += 2
            else:
                value = self.registers.get(address, 0)
                if t == ModbusDataType.INT_16 and value >= 0x8000:
                    value -= 0x10000
                result.append(value)
                address += 1
        return result[0] if single else result


def _registers() -> Dict[int, int]:
    registers = {}
    registers.update({BATTERY_BASE: SUNS_MARKER >> 16, BATTERY_BASE + 1: SUNS_MARKER & 0xFFFF})
    registers.update({BATTERY_BASE + 2: 802, BATTERY_BASE + 3: 64})
    model_base = BATTERY_BASE + 4
    registers[model_base + points.BATTERY["W"].offset] = (-500) & 0xFFFF
    registers[model_base + points.BATTERY["W"].sf_offset] = 0
    registers[model_base + points.BATTERY["SoC"].offset] = 55
    registers[model_base + points.BATTERY["SoC"].sf_offset] = 0
    terminator = model_base + 64
    registers.update({terminator: 0xFFFF, terminator + 1: 0})
    return registers


def _bat() -> SunspecBat:
    bat = SunspecBat(SunspecBatSetup(), client=FakeSunSpecClient(_registers()), device_id=1)
    bat.initialize()
    bat.peak_filter.check_values = Mock()
    bat.store = Mock()
    return bat


def test_update_reads_soc_and_flips_power_sign():
    bat = _bat()

    bat.update()

    state = bat.store.set.call_args[0][0]
    assert state.power == pytest.approx(500.0)
    assert state.soc == pytest.approx(55.0)


def test_set_power_limit_is_a_harmless_noop():
    bat = _bat()

    bat.set_power_limit(Mock(power_limit=1000))

    assert bat.power_limit_controllable() is False
