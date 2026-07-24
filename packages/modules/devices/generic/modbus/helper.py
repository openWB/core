from typing import Any

from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.devices.generic.modbus.config import RegisterConfig


def check_data(wert):
    if (wert.reg_type is None or
        wert.byteorder is None or
            wert.wordorder is None):
        raise ValueError(
            f"Unvollständige Konfiguration für Universeller-Modbus: Register-Adresse {wert.reg_address}")


def read_value(client: ModbusTcpClient_, unit: int, register_config: RegisterConfig) -> Any:
    if register_config.reg_address is None:
        return None

    check_data(register_config)
    return client.read_input_registers(
        register_config.reg_address,
        ModbusDataType[register_config.reg_type],
        byteorder=register_config.byteorder,
        wordorder=register_config.wordorder,
        unit=unit,
    )


def read_phase_values(client: ModbusTcpClient_, unit: int, *register_configs: RegisterConfig) -> Any:
    values = [0.0] * 3
    has_value = False
    for index, register_config in enumerate(register_configs):
        value = read_value(client, unit, register_config)
        if value is not None:
            values[index] = value
            has_value = True
    return values if has_value else None
