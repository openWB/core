from typing import Dict, Iterable, List, Union

import pytest

from modules.common.modbus import ModbusDataType
from modules.common.sunspec.discovery import (
    SUNS_MARKER, SunSpecDiscoveryError, SunSpecModelLocation, discover_models, require_model
)


class FakeSunSpecClient:
    def __init__(self, registers: Dict[int, int]):
        self.registers = registers

    def read_holding_registers(self, address: int, types: Union[ModbusDataType, Iterable[ModbusDataType]],
                               unit: int = 1) -> Union[int, List[int]]:
        single = isinstance(types, ModbusDataType)
        type_list = [types] if single else list(types)
        result = []
        for t in type_list:
            if t == ModbusDataType.UINT_32:
                high, low = self.registers[address], self.registers[address + 1]
                result.append((high << 16) | low)
                address += 2
            elif t == ModbusDataType.UINT_16:
                result.append(self.registers.get(address, 42))
                address += 1
            else:
                raise NotImplementedError(t)
        return result[0] if single else result


def _suns_marker_registers(base: int) -> Dict[int, int]:
    return {base: SUNS_MARKER >> 16, base + 1: SUNS_MARKER & 0xFFFF}


def _model_header(address: int, model_id: int, length: int) -> Dict[int, int]:
    return {address: model_id, address + 1: length}


def test_discovers_single_model_at_standard_base():
    registers = {}
    registers.update(_suns_marker_registers(40000))
    registers.update(_model_header(40002, model_id=1, length=66))  # Common Model
    registers.update(_model_header(40002 + 2 + 66, model_id=0xFFFF, length=0))  # Terminator

    models = discover_models(FakeSunSpecClient(registers))

    assert models == {1: SunSpecModelLocation(model_id=1, base_address=40004, length=66)}


def test_discovers_chain_of_several_models_in_order():
    registers = {}
    registers.update(_suns_marker_registers(40000))
    address = 40002
    registers.update(_model_header(address, model_id=1, length=66))
    address += 2 + 66
    registers.update(_model_header(address, model_id=113, length=60))  # float Inverter
    inverter_base = address + 2
    address = inverter_base + 60
    registers.update(_model_header(address, model_id=160, length=50))  # Multiple MPPT Extension
    mppt_base = address + 2
    address = mppt_base + 50
    registers.update(_model_header(address, model_id=0xFFFF, length=0))

    models = discover_models(FakeSunSpecClient(registers))

    assert set(models.keys()) == {1, 113, 160}
    assert models[113] == SunSpecModelLocation(model_id=113, base_address=inverter_base, length=60)
    assert models[160] == SunSpecModelLocation(model_id=160, base_address=mppt_base, length=50)


def test_falls_back_to_base_zero_if_40000_has_no_marker():
    registers = {}
    registers.update(_suns_marker_registers(0))
    registers.update(_model_header(2, model_id=1, length=66))
    registers.update(_model_header(2 + 2 + 66, model_id=0xFFFF, length=0))

    models = discover_models(FakeSunSpecClient(registers))

    assert models[1].base_address == 4


def test_no_marker_at_any_candidate_base_raises_clear_error():
    with pytest.raises(SunSpecDiscoveryError, match="Kein SunSpec-Gerät gefunden"):
        discover_models(FakeSunSpecClient({}))


def test_chain_without_terminator_raises_instead_of_looping_forever():
    registers = {}
    registers.update(_suns_marker_registers(40000))
    address = 40002
    # Modellkette mit Länge 0 wiederholt sich an derselben Adresse - ohne Terminator-Erkennung
    # würde das eine Endlosschleife sein.
    registers.update(_model_header(address, model_id=42, length=0))

    with pytest.raises(SunSpecDiscoveryError, match="endet nicht innerhalb von"):
        discover_models(FakeSunSpecClient(registers))


class TestRequireModel:
    def test_returns_first_matching_candidate_in_priority_order(self):
        models = {
            111: SunSpecModelLocation(model_id=111, base_address=40004, length=60),
            101: SunSpecModelLocation(model_id=101, base_address=40200, length=50),
        }

        result = require_model(models, [101, 111], "Inverter")

        assert result.model_id == 101

    def test_raises_clear_error_if_no_candidate_present(self):
        models = {1: SunSpecModelLocation(model_id=1, base_address=40004, length=66)}

        with pytest.raises(SunSpecDiscoveryError, match="Inverter"):
            require_model(models, [101, 103, 111, 113], "Inverter")
