#!/usr/bin/env python3
import logging

from typing import Any, TypedDict, Dict, Union, Optional, Tuple


from pymodbus.constants import Endian
import pymodbus


from modules.common import modbus
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.solaredge.solaredge.config import SolaredgeBatSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType

log = logging.getLogger(__name__)

FLOAT32_UNSUPPORTED = -0xffffff00000000000000000000000000
MAX_CHARGEDISCHARGE_LIMIT = 5000
CONTROL_MODE_MSC = 1  # Storage Control Mode Maximize Self Consumption
CONTROL_MODE_REMOTE = 4  # Control Mode Remotesteuerung
REMOTE_CONTROL_COMMAND_MODE_DEFAULT = 0  # Default RC Command Mode ohne Steuerung
REMOTE_CONTROL_COMMAND_MODE_CHARGE = 3  # RC Command Mode Charge from PV+AC
REMOTE_CONTROL_COMMAND_MODE_MSC = 7  # RC Command Mode Maximize Self Consumtion used for Limit Discharge


class KwargsDict(TypedDict):
    device_id: int
    client: modbus.ModbusTcpClient_


class SolaredgeBat(AbstractBat):
    # Define all possible registers with their data types
    REGISTERS = {
        "Battery1StateOfEnergy": (0xe184, ModbusDataType.FLOAT_32,),  # Mirror: 0xf584
        "Battery1InstantaneousPower": (0xe174, ModbusDataType.FLOAT_32,),  # Mirror: 0xf574
        "Battery2StateOfEnergy": (0xe284, ModbusDataType.FLOAT_32,),
        "Battery2InstantaneousPower": (0xe274, ModbusDataType.FLOAT_32,),
        "StorageControlMode": (0xe004, ModbusDataType.UINT_16,),
        "StorageBackupReserved": (0xe008, ModbusDataType.FLOAT_32,),
        "RemoteControlCommandModeDefault": (0xe00a, ModbusDataType.UINT_16,),
        "RemoteControlCommandMode": (0xe00d, ModbusDataType.UINT_16,),
        "RemoteControlChargeLimit": (0xe00e, ModbusDataType.FLOAT_32,),
        "RemoteControlDischargeLimit": (0xe010, ModbusDataType.FLOAT_32,),
    }

    def __init__(self, component_config: SolaredgeBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.BAT, self.component_config.id, self.fault_state)

    def update(self) -> None:
        self.store.set(self.read_state())

    def read_state(self):
        power, soc = self.get_values()
        self.peak_filter.check_values(power)
        imported, exported = self.get_imported_exported(power)
        return BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )

    def get_values(self) -> Tuple[float, float]:
        unit = self.component_config.configuration.modbus_id
        # Use 1 as fallback if battery_index is not set
        battery_index = getattr(self.component_config.configuration, "battery_index", 1)

        # Define base registers for Battery 1 in hex
        base_soc_reg = 0xE184  # Battery 1 SoC
        base_power_reg = 0xE174  # Battery 1 Power
        offset = 0x100  # 256 bytes in hex

        # Adjust registers based on battery_index
        if battery_index == 1:
            soc_reg = base_soc_reg
            power_reg = base_power_reg
        elif battery_index == 2:
            soc_reg = base_soc_reg + offset  # 0xE284
            power_reg = base_power_reg + offset  # 0xE274
        else:
            raise ValueError(f"Invalid battery_index: {battery_index}. Must be 1 or 2.")

        # Read SoC and Power from the appropriate registers
        soc = self.__tcp_client.read_holding_registers(
            soc_reg, ModbusDataType.FLOAT_32, wordorder=Endian.Little, unit=unit
        )
        power = self.__tcp_client.read_holding_registers(
            power_reg, ModbusDataType.FLOAT_32, wordorder=Endian.Little, unit=unit
        )

        # Handle unsupported case
        if power == FLOAT32_UNSUPPORTED:
            power = 0
        if soc == FLOAT32_UNSUPPORTED or not 0 <= soc <= 100:
            log.warning(f"Invalid SoC Speicher{battery_index}: {soc}")

        return power, soc

    def get_imported_exported(self, power: float) -> Tuple[float, float]:
        return self.sim_counter.sim_count(power)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        unit = self.component_config.configuration.modbus_id
        # Use 1 as fallback if battery_index is not set
        battery_index = getattr(self.component_config.configuration, "battery_index", 1)

        registers_to_read = [
            "StorageControlMode",
            "RemoteControlCommandMode",
            "RemoteControlChargeLimit",
            "RemoteControlDischargeLimit",
        ]
        try:
            values = self._read_registers(registers_to_read, unit)
        except pymodbus.exceptions.ModbusException as e:
            log.error(f"Failed to read registers: {e}")
            self.fault_state.error(f"Modbus read error: {e}")
            return

        if power_limit is None:  # No Bat Control should be used.
            if values["StorageControlMode"] == CONTROL_MODE_MSC:
                log.debug(f"Speicher{battery_index}:Keine Steuerung gefordert, bereits deaktiviert.")
            else:
                # Disable Bat Control
                values_to_write = {
                    "RemoteControlChargeLimit": MAX_CHARGEDISCHARGE_LIMIT,
                    "RemoteControlDischargeLimit": MAX_CHARGEDISCHARGE_LIMIT,
                    "RemoteControlCommandModeDefault": REMOTE_CONTROL_COMMAND_MODE_DEFAULT,
                    "RemoteControlCommandMode": REMOTE_CONTROL_COMMAND_MODE_DEFAULT,
                    "StorageControlMode": CONTROL_MODE_MSC,
                }
                self._write_registers(values_to_write, unit)
                log.debug(f"Speicher{battery_index}:Keine Steuerung gefordert, Steuerung deaktiviert.")

        elif power_limit <= 0:  # Limit Discharge Mode should be used.
            if (values["StorageControlMode"] == CONTROL_MODE_REMOTE and
                    values["RemoteControlCommandMode"] == REMOTE_CONTROL_COMMAND_MODE_MSC):
                # Remote Control and Discharge Mode already active.
                discharge_limit = int(values["RemoteControlDischargeLimit"])
                if discharge_limit not in range(int(abs(power_limit)) - 10, int(abs(power_limit)) + 10):
                    # Send Limit only if difference is more than 10W, needed with more than 1 battery.
                    values_to_write = {
                        "RemoteControlDischargeLimit": int(min(abs(power_limit), MAX_CHARGEDISCHARGE_LIMIT))
                    }
                    self._write_registers(values_to_write, unit)
                    log.debug(f"Entlade-Limit Speicher{battery_index}: {int(abs(power_limit))}W.")
                else:
                    log.debug(f"Entlade-Limit Speicher{battery_index}: Abweichung unter  +/- 10W.")
            else:  # Enable Remote Control and Discharge Mode.
                values_to_write = {
                    "StorageControlMode": CONTROL_MODE_REMOTE,
                    "RemoteControlCommandModeDefault": REMOTE_CONTROL_COMMAND_MODE_MSC,
                    "RemoteControlCommandMode": REMOTE_CONTROL_COMMAND_MODE_MSC,
                    "RemoteControlDischargeLimit": int(min(abs(power_limit), MAX_CHARGEDISCHARGE_LIMIT))
                }
                self._write_registers(values_to_write, unit)
                log.debug(f"Entlade-Limit aktiviert, Speicher{battery_index}: {int(abs(power_limit))}W.")

        elif power_limit > 0:  # Charge Mode should be used
            if (values["StorageControlMode"] == CONTROL_MODE_REMOTE and
                    values["RemoteControlCommandMode"] == REMOTE_CONTROL_COMMAND_MODE_CHARGE):
                # Remote Control and Charge Mode already active.
                charge_limit = int(values["RemoteControlChargeLimit"])
                if charge_limit not in range(int(abs(power_limit)) - 10, int(abs(power_limit)) + 10):
                    # Send Limit only if difference is more than 10W.
                    values_to_write = {
                        "RemoteControlChargeLimit": int(min(abs(power_limit), MAX_CHARGEDISCHARGE_LIMIT))
                    }
                    self._write_registers(values_to_write, unit)
                    log.debug(f"Ladung Speicher{battery_index}: {int(abs(power_limit))}W.")
                else:
                    log.debug(f"Ladung Speicher{battery_index}: Abweichung unter  +/- 10W.")
            else:  # Enable Remote Control and Charge Mode.
                values_to_write = {
                    "StorageControlMode": CONTROL_MODE_REMOTE,
                    "RemoteControlCommandModeDefault": REMOTE_CONTROL_COMMAND_MODE_CHARGE,
                    "RemoteControlCommandMode": REMOTE_CONTROL_COMMAND_MODE_CHARGE,
                    "RemoteControlChargeLimit": int(min(abs(power_limit), MAX_CHARGEDISCHARGE_LIMIT))
                }
                self._write_registers(values_to_write, unit)
                log.debug(f"Aktivierung Ladung Speicher{battery_index}: {int(abs(power_limit))}W.")

    def _read_registers(self, register_names: list, unit: int) -> Dict[str, Union[int, float]]:
        values = {}
        for key in register_names:
            address, data_type = self.REGISTERS[key]
            try:
                values[key] = self.__tcp_client.read_holding_registers(
                    address, data_type, wordorder=Endian.Little, unit=unit
                )
            except pymodbus.exceptions.ModbusException as e:
                log.error(f"Failed to read register {key} at address {address}: {e}")
                self.fault_state.error(f"Modbus read error: {e}")
                values[key] = 0  # Fallback value
        log.debug(f"Bat raw values {self.__tcp_client.address}: {values}")
        return values
        # TODO: Optimize to read multiple contiguous registers in a single request if supported by ModbusTcpClient_

    def _write_registers(self, values_to_write: Dict[str, Union[int, float]], unit: int) -> None:
        for key, value in values_to_write.items():
            address, data_type = self.REGISTERS[key]
            try:
                self.__tcp_client.write_register(address, value, data_type, wordorder=Endian.Little, unit=unit)
                log.debug(f"Neuer Wert {value} in Register {address} geschrieben.")
            except pymodbus.exceptions.ModbusException as e:
                log.error(f"Failed to write register {key} at address {address}: {e}")
                self.fault_state.error(f"Modbus write error: {e}")

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=SolaredgeBatSetup)
