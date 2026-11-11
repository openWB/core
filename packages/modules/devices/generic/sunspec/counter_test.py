import struct
from typing import Dict, Union
from unittest.mock import Mock

import pytest

from modules.common.modbus import ModbusDataType
from modules.common.sunspec import points
from modules.common.sunspec.discovery import SUNS_MARKER
from modules.devices.generic.sunspec.config import SunspecCounterSetup
from modules.devices.generic.sunspec.counter import SunspecCounter


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


def _registers_with_float_meter(base: int, values: Dict[str, float]) -> Dict[int, int]:
    registers = {base: SUNS_MARKER >> 16, base + 1: SUNS_MARKER & 0xFFFF}
    registers.update({base + 2: 213, base + 3: 124})
    model_base = base + 4
    for name, value in values.items():
        offset = points.METER_FLOAT[name].offset
        high, low = struct.unpack(">HH", struct.pack(">f", value))
        registers[model_base + offset], registers[model_base + offset + 1] = high, low
    registers.update({model_base + 124: 0xFFFF, model_base + 125: 0})
    return registers


def _meter_model_registers(header: int, w: int, w_sf: int, exported: int, imported: int,
                           energy_sf: int) -> Dict[int, int]:
    registers = {header: 203, header + 1: 105}
    model_base = header + 2
    registers[model_base + points.METER_INT_SF["W"].offset] = w & 0xFFFF
    registers[model_base + points.METER_INT_SF["W"].sf_offset] = w_sf & 0xFFFF
    exp_offset = points.METER_INT_SF["TotWhExp"].offset
    registers[model_base + exp_offset] = exported >> 16
    registers[model_base + exp_offset + 1] = exported & 0xFFFF
    imp_offset = points.METER_INT_SF["TotWhImp"].offset
    registers[model_base + imp_offset] = imported >> 16
    registers[model_base + imp_offset + 1] = imported & 0xFFFF
    registers[model_base + points.METER_INT_SF["TotWhExp"].sf_offset] = energy_sf & 0xFFFF
    registers.update({model_base + 105: 0xFFFF, model_base + 106: 0})
    return registers


def _registers_with_int_sf_meter(base: int, w: int, w_sf: int, exported: int, imported: int,
                                 energy_sf: int) -> Dict[int, int]:
    registers = {base: SUNS_MARKER >> 16, base + 1: SUNS_MARKER & 0xFFFF}
    registers.update(_meter_model_registers(base + 2, w, w_sf, exported, imported, energy_sf))
    return registers


def _common_model_registers(header: int, manufacturer: str) -> Dict[int, int]:
    registers = {header: 1, header + 1: 16}
    text = manufacturer.encode("ascii").ljust(32, b"\x00")
    model_base = header + 2
    for i in range(16):
        registers[model_base + i] = (text[2 * i] << 8) | text[2 * i + 1]
    return registers


def _counter(registers: Dict[int, int]) -> SunspecCounter:
    counter = SunspecCounter(SunspecCounterSetup(), client=FakeSunSpecClient(registers), device_id=1)
    counter.initialize()
    counter.peak_filter.check_values = Mock(side_effect=lambda power, imp, exp: (imp, exp))
    counter.store = Mock()
    return counter


def test_reads_all_fields_from_float_meter_model():
    registers = _registers_with_float_meter(40000, {
        "W": -500.0, "WphA": -166.0, "WphB": -167.0, "WphC": -167.0,
        "AphA": -1.1, "AphB": -1.2, "AphC": -1.3,
        "PhVphA": 230.0, "PhVphB": 231.0, "PhVphC": 232.0,
        "PFphA": 0.9, "PFphB": 0.91, "PFphC": 0.92,
        "Hz": 50.0, "TotWhExp": 1200000.0, "TotWhImp": 300000.0,
    })

    counter = _counter(registers)
    counter.update()

    state = counter.store.set.call_args[0][0]
    assert state.power == pytest.approx(-500.0)
    assert state.powers == [pytest.approx(-166.0), pytest.approx(-167.0), pytest.approx(-167.0)]
    assert state.currents == [pytest.approx(-1.1), pytest.approx(-1.2), pytest.approx(-1.3)]
    assert state.voltages == [pytest.approx(230.0), pytest.approx(231.0), pytest.approx(232.0)]
    assert state.power_factors == [pytest.approx(0.9), pytest.approx(0.91), pytest.approx(0.92)]
    assert state.frequency == pytest.approx(50.0)
    assert state.exported == pytest.approx(1200000.0)
    assert state.imported == pytest.approx(300000.0)


def test_reads_power_and_energy_from_int_sf_meter_model():
    registers = _registers_with_int_sf_meter(
        40000, w=-5000, w_sf=-1, exported=12000000, imported=3000000, energy_sf=-1)

    counter = _counter(registers)
    counter.update()

    state = counter.store.set.call_args[0][0]
    assert state.power == pytest.approx(-500.0)
    assert state.exported == pytest.approx(1200000.0)
    assert state.imported == pytest.approx(300000.0)


def test_int_sf_meter_power_factor_is_percentage_scaled_to_ratio():
    registers = _registers_with_int_sf_meter(
        40000, w=-5000, w_sf=-1, exported=12000000, imported=3000000, energy_sf=-1)
    model_base = 40000 + 2 + 2
    registers[model_base + points.METER_INT_SF["PFphA"].offset] = 95
    registers[model_base + points.METER_INT_SF["PFphA"].sf_offset] = 0

    counter = _counter(registers)
    counter.update()

    assert counter.store.set.call_args[0][0].power_factors[0] == pytest.approx(0.95)


def test_single_phase_meter_with_unimplemented_phases_does_not_crash():
    registers = _registers_with_int_sf_meter(
        40000, w=-5000, w_sf=-1, exported=12000000, imported=3000000, energy_sf=-1)
    model_base = 40000 + 2 + 2
    registers[model_base + points.METER_INT_SF["AphA"].offset] = 10
    registers[model_base + points.METER_INT_SF["AphA"].sf_offset] = 0
    registers[model_base + points.METER_INT_SF["PhVphA"].offset] = 2400
    registers[model_base + points.METER_INT_SF["PhVphA"].sf_offset] = -1
    registers[model_base + points.METER_INT_SF["WphA"].offset] = -5000 & 0xFFFF
    for name in ("AphB", "AphC", "PhVphB", "PhVphC", "WphB", "WphC", "PFphB", "PFphC"):
        registers[model_base + points.METER_INT_SF[name].offset] = 0x8000

    counter = _counter(registers)
    counter.update()

    state = counter.store.set.call_args[0][0]
    assert state.currents == [pytest.approx(-10.0), 0.0, 0.0]
    assert state.voltages == [pytest.approx(240.0), 230.0, 230.0]
    assert state.powers == [pytest.approx(-500.0), 0.0, 0.0]
    assert state.power_factors == [0.0, 0.0, 0.0]


def test_fronius_meter_power_direction_is_inverted():
    registers = _common_model_registers(40000 + 2, "Fronius")
    registers.update({40000: SUNS_MARKER >> 16, 40000 + 1: SUNS_MARKER & 0xFFFF})
    registers.update(_meter_model_registers(
        40000 + 2 + 18, w=-5000, w_sf=-1, exported=12000000, imported=3000000, energy_sf=-1))

    counter = _counter(registers)
    counter.update()

    assert counter.store.set.call_args[0][0].power == pytest.approx(500.0)
