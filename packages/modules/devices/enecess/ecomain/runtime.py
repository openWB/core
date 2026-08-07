import math
import time
from dataclasses import dataclass
from typing import Callable, Iterable, Union

from modules.common.modbus import (
    Endian,
    ModbusDataType,
    ModbusTcpClient_,
    Number,
)


UNIT_ID = 255
MIN_SOFTWARE_VERSION = 138
RETRY_INTERVAL = 300
POWER_FACTOR = 0.01
ELECTRICAL_FACTOR = 0.01
ENERGY_FACTOR = 0.001


class EcoMainCompatibilityError(Exception):
    pass


@dataclass(frozen=True)
class EcoMainCounterReading:
    power: float
    powers: list[float]
    voltages: list[float]
    currents: list[float]
    power_factors: list[float]
    imported: float
    exported: float


@dataclass(frozen=True)
class EcoMainChannelReading:
    power: float
    current: float
    forward_energy: float
    reverse_energy: float


class EcoMainRuntime:
    def __init__(
            self,
            ip_address: str,
            configured_serial: str,
            client: ModbusTcpClient_ = None,
            clock: Callable[[], float] = time.monotonic):
        self.client = client or ModbusTcpClient_(ip_address)
        self._configured_serial = configured_serial
        self._clock = clock
        self._device_serial = ""
        self._validated = False
        self._last_error = None
        self._next_retry_at = 0.0

    @property
    def device_serial(self) -> str:
        return self._device_serial

    @staticmethod
    def decode_serial(registers: Iterable[int]) -> str:
        serial_bytes = bytearray()
        for register in registers:
            serial_bytes.append(register & 0xFF)
            serial_bytes.append((register >> 8) & 0xFF)
        return serial_bytes.decode("ascii", errors="strict")

    @staticmethod
    def channel_addresses(source: int, channel: int) -> tuple[int, int, int, int]:
        if not 0 <= source <= 3:
            raise ValueError("Die EcoMain-Quelle muss zwischen 0 und 3 liegen.")
        if not 1 <= channel <= 10:
            raise ValueError("Der EcoMain-Kanal muss zwischen 1 und 10 liegen.")
        channel_offset = channel - 1
        return (
            1008 + source * 20 + channel_offset * 2,
            1210 + source * 30 + channel_offset * 3,
            32 + source * 40 + channel_offset * 4,
            192 + source * 40 + channel_offset * 4,
        )

    def ensure_compatible(self) -> None:
        if self._validated:
            return
        now = self._clock()
        if self._last_error is not None and now < self._next_retry_at:
            remaining = math.ceil(self._next_retry_at - now)
            raise EcoMainCompatibilityError(
                f"EcoMain-Kompatibilitätsprüfung fehlgeschlagen: {self._last_error} "
                f"Erneuter Versuch in {remaining} Sekunden."
            )
        try:
            with self.client:
                version = self._read(3009, ModbusDataType.UINT_16)
                serial = self.decode_serial(
                    self._read(3002, [ModbusDataType.UINT_16] * 6)
                )
            if version < MIN_SOFTWARE_VERSION:
                raise EcoMainCompatibilityError(
                    f"EcoMain-Softwareversion {version} wird nicht unterstützt. "
                    f"Mindestens Version {MIN_SOFTWARE_VERSION} ist erforderlich."
                )
            if serial != self._configured_serial:
                raise EcoMainCompatibilityError(
                    f"Die konfigurierte Seriennummer {self._configured_serial} stimmt nicht mit "
                    f"der EcoMain-Seriennummer {serial} überein."
                )
        except Exception as exc:
            self._last_error = str(exc)
            self._next_retry_at = now + RETRY_INTERVAL
            if isinstance(exc, EcoMainCompatibilityError):
                raise
            raise EcoMainCompatibilityError(
                f"EcoMain konnte nicht geprüft werden: {exc}"
            ) from exc
        self._device_serial = serial
        self._validated = True
        self._last_error = None

    def read_counter(self) -> EcoMainCounterReading:
        imported = self._read(12, ModbusDataType.INT_64)
        exported = self._read(28, ModbusDataType.INT_64)
        raw_powers = self._read(1000, [ModbusDataType.INT_32] * 4)
        raw_electrical = self._read(
            1200,
            [ModbusDataType.UINT_16, ModbusDataType.UINT_16,
             ModbusDataType.INT_16] * 3,
        )
        return EcoMainCounterReading(
            power=raw_powers[3] * POWER_FACTOR,
            powers=[value * POWER_FACTOR for value in raw_powers[:3]],
            voltages=[value * ELECTRICAL_FACTOR for value in raw_electrical[0::3]],
            currents=[value * ELECTRICAL_FACTOR for value in raw_electrical[1::3]],
            power_factors=[value * ELECTRICAL_FACTOR for value in raw_electrical[2::3]],
            imported=imported * ENERGY_FACTOR,
            exported=exported * ENERGY_FACTOR,
        )

    def read_channel(self, source: int, channel: int) -> EcoMainChannelReading:
        power_address, current_address, forward_address, reverse_address = \
            self.channel_addresses(source, channel)
        power = self._read(power_address, ModbusDataType.INT_32)
        current = self._read(current_address, ModbusDataType.UINT_16)
        forward_energy = self._read(forward_address, ModbusDataType.INT_64)
        reverse_energy = self._read(reverse_address, ModbusDataType.INT_64)
        return EcoMainChannelReading(
            power=power * POWER_FACTOR,
            current=current * ELECTRICAL_FACTOR,
            forward_energy=forward_energy * ENERGY_FACTOR,
            reverse_energy=reverse_energy * ENERGY_FACTOR,
        )

    def _read(
            self,
            address: int,
            types: Union[Iterable[ModbusDataType], ModbusDataType]) -> Union[Number, list[Number]]:
        return self.client.read_holding_registers(
            address,
            types,
            unit=UNIT_ID,
            byteorder=Endian.Big,
            wordorder=Endian.Little,
        )
