from enum import Enum
from typing import TypedDict
from modules.common.modbus import ModbusDataType


class OutputDict(TypedDict):
    name: str
    live_zero_factor: float


class OutputType(Enum):
    VOLTAGE = OutputDict(name="voltage", live_zero_factor=0.1)  # (0)1-10V
    CURRENT = OutputDict(name="current", live_zero_factor=0.2)  # (0)4-20mA


class ModelDict(TypedDict):
    name: str
    output_type: OutputType
    min_value: int
    max_value: int
    register: int
    data_type: ModbusDataType


def model_dict(name: str, output_type: OutputType, min_value: int, max_value: int,
               register: int, data_type: ModbusDataType) -> ModelDict:
    return {
        "name": name,
        "output_type": output_type,
        "min_value": min_value,
        "max_value": max_value,
        "register": register,
        "data_type": data_type
    }


class Model(Enum):
    N4Dac02 = model_dict("N4Dac02", OutputType.VOLTAGE, 0, 1000, 1, ModbusDataType.INT_16)
    DA02 = model_dict("DA02", OutputType.VOLTAGE, 0, 4000, 500, ModbusDataType.INT_16)
    M120T_AO1 = model_dict("M120T-1", OutputType.VOLTAGE, 0, 4095, 0, ModbusDataType.INT_16)
    M120T_AO2 = model_dict("M120T-2", OutputType.VOLTAGE, 0, 4095, 1, ModbusDataType.INT_16)
    AA02B = model_dict("AA02B", OutputType.CURRENT, 0, 4095, 500, ModbusDataType.INT_16)
