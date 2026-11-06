"""Liest einen einzelnen SunSpec-Punkt (siehe points.py) aus einem per Discovery gefundenen
Modell. int16/uint16/acc32-Punkte werden mit ihrem sunssf-Skalierungsfaktor-Register gelesen
und skaliert (raw * 10**sf), float32-Punkte direkt gelesen. "Not implemented"-Sentinelwerte
(SunSpec-Spezifikation: 0x8000 bei int16, 0xFFFF bei uint16, NaN bei float32) werden als None
zurückgegeben - acc32 kennt laut Spezifikation keinen solchen Sentinel.
"""
import math
from typing import Optional

from modules.common.modbus import ModbusClient, ModbusDataType
from modules.common.sunspec.discovery import SunSpecModelLocation
from modules.common.sunspec.points import Point

NOT_IMPLEMENTED_INT16 = -32768
NOT_IMPLEMENTED_UINT16 = 0xFFFF

_RAW_TYPE = {
    "int16": ModbusDataType.INT_16,
    "uint16": ModbusDataType.UINT_16,
    "acc32": ModbusDataType.UINT_32,
}


def read_point(client: ModbusClient, model: SunSpecModelLocation, point: Point, unit: int = 1) -> Optional[float]:
    address = model.base_address + point.offset
    if point.type == "float32":
        value = client.read_holding_registers(address, ModbusDataType.FLOAT_32, unit=unit)
        return None if math.isnan(value) else value

    raw = client.read_holding_registers(address, _RAW_TYPE[point.type], unit=unit)
    if point.type == "int16" and raw == NOT_IMPLEMENTED_INT16:
        return None
    if point.type == "uint16" and raw == NOT_IMPLEMENTED_UINT16:
        return None
    sf = client.read_holding_registers(model.base_address + point.sf_offset, ModbusDataType.INT_16, unit=unit)
    return raw * (10 ** sf)
