from dataclasses import FrozenInstanceError
from pathlib import Path
import subprocess
import sys
from unittest.mock import MagicMock, call

import pytest

from modules.common.modbus import Endian, ModbusDataType, ModbusTcpClient_
from modules.devices.enecess.ecomain.runtime import (
    EcoMainChannelReading,
    EcoMainCompatibilityError,
    EcoMainCounterReading,
    EcoMainRuntime,
)


SERIAL_REGISTERS = [0x3930, 0x3839, 0x3630, 0x3735, 0x3331, 0x3033]
READ_KWARGS = {
    "unit": 255,
    "byteorder": Endian.Big,
    "wordorder": Endian.Little,
}


def make_client(*responses):
    client = MagicMock(spec=ModbusTcpClient_)
    client.read_holding_registers.side_effect = responses
    return client


def test_runtime_import_does_not_load_device_module():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; "
            "from modules.devices.enecess.ecomain.runtime import EcoMainRuntime; "
            "assert 'modules.devices.enecess.ecomain.device' not in sys.modules",
        ],
        cwd=Path(__file__).resolve().parents[4],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_serial_registers_preserve_leading_zeroes():
    assert EcoMainRuntime.decode_serial(SERIAL_REGISTERS) == "099806571330"


@pytest.mark.parametrize("source,channel,expected", [
    (0, 1, (1008, 1210, 32, 192)),
    (0, 10, (1026, 1237, 68, 228)),
    (1, 1, (1028, 1240, 72, 232)),
    (3, 10, (1086, 1327, 188, 348)),
])
def test_channel_addresses(source, channel, expected):
    assert EcoMainRuntime.channel_addresses(source, channel) == expected


@pytest.mark.parametrize("source,channel", [
    (-1, 1),
    (4, 1),
    (0, 0),
    (0, 11),
])
def test_channel_addresses_reject_invalid_ranges(source, channel):
    with pytest.raises(ValueError):
        EcoMainRuntime.channel_addresses(source, channel)


def test_successful_compatibility_check_is_cached():
    client = make_client(138, SERIAL_REGISTERS)
    runtime = EcoMainRuntime("192.0.2.1", "099806571330", client=client)

    runtime.ensure_compatible()
    runtime.ensure_compatible()

    client.__enter__.assert_called_once_with()
    client.__exit__.assert_called_once()
    assert client.read_holding_registers.call_count == 2
    assert runtime.device_serial == "099806571330"
    assert client.read_holding_registers.call_args_list == [
        call(3009, ModbusDataType.UINT_16, **READ_KWARGS),
        call(3002, [ModbusDataType.UINT_16] * 6, **READ_KWARGS),
    ]


def test_unsupported_version_is_cached_until_retry_interval():
    now = [0]
    client = make_client(137, SERIAL_REGISTERS, 137, SERIAL_REGISTERS)
    runtime = EcoMainRuntime(
        "192.0.2.1", "099806571330", client=client, clock=lambda: now[0]
    )

    with pytest.raises(EcoMainCompatibilityError) as first_error:
        runtime.ensure_compatible()
    assert str(first_error.value) == (
        "EcoMain-Softwareversion 137 wird nicht unterstützt. "
        "Mindestens Version 138 ist erforderlich."
    )
    assert client.read_holding_registers.call_count == 2

    now[0] = 299
    with pytest.raises(EcoMainCompatibilityError) as cached_error:
        runtime.ensure_compatible()
    assert str(cached_error.value) == (
        "EcoMain-Kompatibilitätsprüfung fehlgeschlagen: "
        "EcoMain-Softwareversion 137 wird nicht unterstützt. "
        "Mindestens Version 138 ist erforderlich. "
        "Erneuter Versuch in 1 Sekunden."
    )
    assert client.read_holding_registers.call_count == 2

    now[0] = 300
    with pytest.raises(EcoMainCompatibilityError):
        runtime.ensure_compatible()
    assert client.read_holding_registers.call_count == 4


def test_serial_mismatch_message_includes_configured_and_detected_serials():
    client = make_client(138, SERIAL_REGISTERS)
    runtime = EcoMainRuntime("192.0.2.1", "079632375788", client=client)

    with pytest.raises(EcoMainCompatibilityError) as error:
        runtime.ensure_compatible()

    assert str(error.value) == (
        "Die konfigurierte Seriennummer 079632375788 stimmt nicht mit "
        "der EcoMain-Seriennummer 099806571330 überein."
    )


def test_modbus_error_is_wrapped_for_compatibility_check():
    client = make_client(OSError("Verbindung getrennt"))
    runtime = EcoMainRuntime("192.0.2.1", "099806571330", client=client)

    with pytest.raises(EcoMainCompatibilityError) as error:
        runtime.ensure_compatible()

    assert str(error.value) == (
        "EcoMain konnte nicht geprüft werden: Verbindung getrennt"
    )
    assert isinstance(error.value.__cause__, OSError)


def test_counter_reading_is_scaled_and_uses_required_register_layout():
    raw_powers = [10000, -2000, 3000, 11000]
    raw_electrical = [
        23000, 123, 99,
        23100, 234, 98,
        23200, 345, 97,
    ]
    client = make_client(1_234_000, 55_000, raw_powers, raw_electrical)
    runtime = EcoMainRuntime("192.0.2.1", "099806571330", client=client)

    reading = runtime.read_counter()

    assert reading == EcoMainCounterReading(
        power=110,
        powers=[100, -20, 30],
        voltages=[230, 231, 232],
        currents=[1.23, 2.34, 3.45],
        power_factors=[0.99, 0.98, 0.97],
        imported=1234,
        exported=55,
    )
    assert client.read_holding_registers.call_args_list == [
        call(12, ModbusDataType.INT_64, **READ_KWARGS),
        call(28, ModbusDataType.INT_64, **READ_KWARGS),
        call(1000, [ModbusDataType.INT_32] * 4, **READ_KWARGS),
        call(1200, [ModbusDataType.UINT_16, ModbusDataType.UINT_16,
                    ModbusDataType.INT_16] * 3, **READ_KWARGS),
    ]


def test_channel_reading_is_scaled_and_uses_calculated_addresses():
    client = make_client(12_345, 678, 9_876_000, 54_000)
    runtime = EcoMainRuntime("192.0.2.1", "099806571330", client=client)

    reading = runtime.read_channel(source=1, channel=1)

    assert reading == EcoMainChannelReading(
        power=123.45,
        current=6.78,
        forward_energy=9876,
        reverse_energy=54,
    )
    assert client.read_holding_registers.call_args_list == [
        call(1028, ModbusDataType.INT_32, **READ_KWARGS),
        call(1240, ModbusDataType.UINT_16, **READ_KWARGS),
        call(72, ModbusDataType.INT_64, **READ_KWARGS),
        call(232, ModbusDataType.INT_64, **READ_KWARGS),
    ]


@pytest.mark.parametrize("reading", [
    EcoMainCounterReading(0, [], [], [], [], 0, 0),
    EcoMainChannelReading(0, 0, 0, 0),
])
def test_readings_are_immutable(reading):
    with pytest.raises(FrozenInstanceError):
        reading.power = 1
