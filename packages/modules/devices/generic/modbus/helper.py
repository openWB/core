from typing import Any

from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.devices.generic.modbus.config import RegisterConfig, GenericModbusConfiguration


def check_data(register_config: RegisterConfig, device_config: GenericModbusConfiguration):
    if (register_config.reg_type is None or
        register_config.reg_factor is None or
        device_config.byteorder is None or
            device_config.wordorder is None):
        raise ValueError(
            f"Unvollständige Konfiguration für Universeller-Modbus: Register-Adresse {register_config.reg_address}")


def read_value(client: ModbusTcpClient_, unit: int,
               device_config: GenericModbusConfiguration,
               register_config: RegisterConfig) -> Any:
    if register_config.reg_address is None:
        return None

    check_data(register_config, device_config)
    value = client.read_input_registers(
        register_config.reg_address,
        ModbusDataType[register_config.reg_type],
        byteorder=device_config.byteorder,
        wordorder=device_config.wordorder,
        unit=unit,
    )

    if register_config.reg_factor is not None and register_config.reg_factor != 1:
        value = value * register_config.reg_factor
    return value


def read_phase_values(client: ModbusTcpClient_,
                      unit: int,
                      device_config: GenericModbusConfiguration,
                      *register_configs: RegisterConfig) -> Any:
    values = [0.0] * 3
    has_value = False
    for index, register_config in enumerate(register_configs):
        value = read_value(client, unit, device_config, register_config)
        if value is not None:
            values[index] = value
            has_value = True
    return values if has_value else None
