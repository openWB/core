#!/usr/bin/env python3
from enum import IntEnum
import logging
from typing import Any, TypedDict, Dict, Union, Optional, Tuple
from pymodbus.constants import Endian

from modules.common import modbus
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.solaredge.solaredge.config import SolaredgeBatSetup

log = logging.getLogger(__name__)

FLOAT32_UNSUPPORTED = -0xFFFFFF00
MAX_CHARGEDISCHARGE_LIMIT = 5000
DEFAULT_SOC = 50.0  # Fallback bei ungültigem SoC
CONTROL_MODE_MSC = 1  # Storage Control Mode Maximize Self Consumption
CONTROL_MODE_REMOTE = 4  # Control Mode Remotesteuerung
REMOTE_CONTROL_COMMAND_MODE_DEFAULT = 0  # Default RC Command Mode ohne Steuerung
REMOTE_CONTROL_COMMAND_MODE_CHARGE = 3  # RC Command Mode Charge from PV+AC
REMOTE_CONTROL_COMMAND_MODE_MSC = 7  # RC Command Mode Maximize Self Consumtion used for Limit Discharge


class KwargsDict(TypedDict):
    device_id: int
    client: modbus.ModbusTcpClient_


class Registers(IntEnum):
    STORAGE_CONTROL_MODE = 0xe004
    REMOTE_CONTROL_COMMAND_MODE_DEFAULT_REG = 0xe00a
    REMOTE_CONTROL_COMMAND_MODE = 0xe00d
    REMOTE_CONTROL_CHARGE_LIMIT = 0xe00e
    REMOTE_CONTROL_DISCHARGE_LIMIT = 0xe010
    BAT_1_POWER = 0xe174
    BAT_1_SOC = 0xe184
    BAT_2_POWER = 0xe274
    BAT_2_SOC = 0xe284


WRITING_DATA_TYPES = {
    Registers.STORAGE_CONTROL_MODE: ModbusDataType.UINT_16,
    Registers.REMOTE_CONTROL_COMMAND_MODE_DEFAULT_REG: ModbusDataType.UINT_16,
    Registers.REMOTE_CONTROL_COMMAND_MODE: ModbusDataType.UINT_16,
    Registers.REMOTE_CONTROL_CHARGE_LIMIT: ModbusDataType.FLOAT_32,
    Registers.REMOTE_CONTROL_DISCHARGE_LIMIT: ModbusDataType.FLOAT_32,
}


class SolaredgeBat(AbstractBat):
    def __init__(self, component_config: SolaredgeBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        self.store.set(self.read_state())

    def read_state(self):
        power, soc = self.get_values()
        imported, exported = self.get_imported_exported(power)
        return BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )

    def get_values(self) -> Tuple[float, float]:
        unit = self.component_config.configuration.modbus_id
        battery_index = getattr(self.component_config.configuration, "battery_index", 1)
        power_reg = Registers.BAT_1_POWER if battery_index == 1 else Registers.BAT_2_POWER
        soc_reg = Registers.BAT_1_SOC if battery_index == 1 else Registers.BAT_2_SOC
        bulk = (
            (power_reg, ModbusDataType.FLOAT_32),
            (soc_reg, ModbusDataType.FLOAT_32),
        )

        resp = self.__tcp_client.read_holding_registers_bulk(
            power_reg, 18, mapping=bulk,  wordorder=Endian.Little, unit=unit)
        log.debug(f"Bat raw values {self.__tcp_client.address}: {resp}")
        power = resp[power_reg]
        soc = resp[soc_reg]
        # Handle unsupported case
        if power == FLOAT32_UNSUPPORTED:
            power = 0
        if soc == FLOAT32_UNSUPPORTED or not 0 <= soc <= 100:
            log.warning(f"Invalid SoC Speicher{battery_index}: {soc}, using default")
            soc = DEFAULT_SOC

        return power, soc

    def get_imported_exported(self, power: float) -> Tuple[float, float]:
        return self.sim_counter.sim_count(power)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        unit = self.component_config.configuration.modbus_id
        battery_index = getattr(self.component_config.configuration, "battery_index", 1)

        bulk = (
            (Registers.STORAGE_CONTROL_MODE, ModbusDataType.UINT_16),
            (Registers.REMOTE_CONTROL_COMMAND_MODE_DEFAULT_REG, ModbusDataType.UINT_16),
            (Registers.REMOTE_CONTROL_COMMAND_MODE, ModbusDataType.UINT_16),
            (Registers.REMOTE_CONTROL_CHARGE_LIMIT, ModbusDataType.FLOAT_32),
            (Registers.REMOTE_CONTROL_DISCHARGE_LIMIT, ModbusDataType.FLOAT_32),
        )

        values = self.__tcp_client.read_holding_registers_bulk(
            Registers.STORAGE_CONTROL_MODE, 13, mapping=bulk, unit=unit)
        log.debug(f"Bat raw values {self.__tcp_client.address}: {values}")

        if power_limit is None:  # No Bat Control should be used.
            if values[Registers.STORAGE_CONTROL_MODE] == CONTROL_MODE_MSC:
                log.debug(f"Speicher{battery_index}:Keine Steuerung gefordert, bereits deaktiviert.")
            else:
                # Disable Bat Control
                values_to_write = {
                    Registers.REMOTE_CONTROL_CHARGE_LIMIT: MAX_CHARGEDISCHARGE_LIMIT,
                    Registers.REMOTE_CONTROL_DISCHARGE_LIMIT: MAX_CHARGEDISCHARGE_LIMIT,
                    Registers.REMOTE_CONTROL_COMMAND_MODE_DEFAULT_REG: REMOTE_CONTROL_COMMAND_MODE_DEFAULT,
                    Registers.REMOTE_CONTROL_COMMAND_MODE: REMOTE_CONTROL_COMMAND_MODE_DEFAULT,
                    Registers.STORAGE_CONTROL_MODE: CONTROL_MODE_MSC,
                }
                self._write_registers(values_to_write, unit)
                log.debug(f"Speicher{battery_index}:Keine Steuerung gefordert, Steuerung deaktiviert.")

        elif power_limit <= 0:  # Limit Discharge Mode should be used.
            if (values[Registers.STORAGE_CONTROL_MODE] == CONTROL_MODE_REMOTE and
                    values[Registers.REMOTE_CONTROL_COMMAND_MODE] == REMOTE_CONTROL_COMMAND_MODE_MSC):
                # Remote Control and Discharge Mode already active.
                discharge_limit = int(values[Registers.REMOTE_CONTROL_DISCHARGE_LIMIT])
                if discharge_limit not in range(int(abs(power_limit)) - 10, int(abs(power_limit)) + 10):
                    # Send Limit only if difference is more than 10W, needed with more than 1 battery.
                    values_to_write = {
                        Registers.REMOTE_CONTROL_DISCHARGE_LIMIT: int(min(abs(power_limit), MAX_CHARGEDISCHARGE_LIMIT))
                    }
                    self._write_registers(values_to_write, unit)
                    log.debug(f"Entlade-Limit Speicher{battery_index}: {int(abs(power_limit))}W.")
                else:
                    log.debug(f"Entlade-Limit Speicher{battery_index}: Abweichung unter  +/- 10W.")
            else:  # Enable Remote Control and Discharge Mode.
                values_to_write = {
                    Registers.STORAGE_CONTROL_MODE: CONTROL_MODE_REMOTE,
                    Registers.REMOTE_CONTROL_COMMAND_MODE_DEFAULT_REG: REMOTE_CONTROL_COMMAND_MODE_MSC,
                    Registers.REMOTE_CONTROL_COMMAND_MODE: REMOTE_CONTROL_COMMAND_MODE_MSC,
                    Registers.REMOTE_CONTROL_DISCHARGE_LIMIT: int(min(abs(power_limit), MAX_CHARGEDISCHARGE_LIMIT))
                }
                self._write_registers(values_to_write, unit)
                log.debug(f"Entlade-Limit aktiviert, Speicher{battery_index}: {int(abs(power_limit))}W.")

        elif power_limit > 0:  # Charge Mode should be used
            if (values[Registers.STORAGE_CONTROL_MODE] == CONTROL_MODE_REMOTE and
                    values[Registers.REMOTE_CONTROL_COMMAND_MODE] == REMOTE_CONTROL_COMMAND_MODE_CHARGE):
                # Remote Control and Charge Mode already active.
                charge_limit = int(values[Registers.REMOTE_CONTROL_CHARGE_LIMIT])
                if charge_limit not in range(int(abs(power_limit)) - 10, int(abs(power_limit)) + 10):
                    # Send Limit only if difference is more than 10W.
                    values_to_write = {
                        Registers.REMOTE_CONTROL_CHARGE_LIMIT: int(min(abs(power_limit), MAX_CHARGEDISCHARGE_LIMIT))
                    }
                    self._write_registers(values_to_write, unit)
                    log.debug(f"Ladung Speicher{battery_index}: {int(abs(power_limit))}W.")
                else:
                    log.debug(f"Ladung Speicher{battery_index}: Abweichung unter  +/- 10W.")
            else:  # Enable Remote Control and Charge Mode.
                values_to_write = {
                    Registers.STORAGE_CONTROL_MODE: CONTROL_MODE_REMOTE,
                    Registers.REMOTE_CONTROL_COMMAND_MODE_DEFAULT_REG: REMOTE_CONTROL_COMMAND_MODE_CHARGE,
                    Registers.REMOTE_CONTROL_COMMAND_MODE: REMOTE_CONTROL_COMMAND_MODE_CHARGE,
                    Registers.REMOTE_CONTROL_CHARGE_LIMIT: int(min(abs(power_limit), MAX_CHARGEDISCHARGE_LIMIT))
                }
                self._write_registers(values_to_write, unit)
                log.debug(f"Aktivierung Ladung Speicher{battery_index}: {int(abs(power_limit))}W.")

    def _write_registers(self, values_to_write: Dict[Registers, Union[int, float]], unit: int) -> None:
        for address, value in values_to_write.items():
            self.__tcp_client.write_register(
                address, value, WRITING_DATA_TYPES[address], wordorder=Endian.Little, unit=unit)
            log.debug(f"Neuer Wert {value} in Register {address} geschrieben.")

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=SolaredgeBatSetup)
