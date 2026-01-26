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

log = logging.getLogger(__name__)

FLOAT32_UNSUPPORTED = -0xffffff00000000000000000000000000
MAX_CHARGEDISCHARGE_LIMIT = 5000
CONTROL_MODE_MSC = 1  # Storage Control Mode Maximize Self Consumption
CONTROL_MODE_REMOTE = 4  # Control Mode Remotesteuerung
REMOTE_CONTROL_COMMAND_MODE_DEFAULT = 0  # Default RC Command Mode ohne Steuerung
REMOTE_CONTROL_COMMAND_MODE_CHARGE = 3  # RC Command Mode Charge from PV+AC
REMOTE_CONTROL_COMMAND_MODE_MSC = 7  # RC Command Mode Maximize Self Consumtion


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
        self.min_soc = 13
        self.StorageControlMode_Read = CONTROL_MODE_MSC  # Default Control Mode Set to MSC if not Read
        self.last_mode = 'undefined'

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
        else:
            self.min_soc = min(int(soc), int(self.min_soc))
            log.debug(f"Min-SoC Speicher{battery_index}: {int(self.min_soc)}%.")

        return power, soc

    def get_imported_exported(self, power: float) -> Tuple[float, float]:
        return self.sim_counter.sim_count(power)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        unit = self.component_config.configuration.modbus_id
        # Use 1 as fallback if battery_index is not set
        battery_index = getattr(self.component_config.configuration, "battery_index", 1)

        if power_limit is None:  # No Bat Control should be used.
            if self.last_mode in ('discharge-mode', 'charge-mode'):
                # Disable Bat Control
                log.debug(f"Speicher{battery_index}:Keine Steuerung gefordert, Steuerung deaktivieren.")
                values_to_write = {
                    "RemoteControlChargeLimit": MAX_CHARGEDISCHARGE_LIMIT,
                    "RemoteControlDischargeLimit": MAX_CHARGEDISCHARGE_LIMIT,
                    "RemoteControlCommandModeDefault": REMOTE_CONTROL_COMMAND_MODE_DEFAULT,
                    "RemoteControlCommandMode": REMOTE_CONTROL_COMMAND_MODE_DEFAULT,
                    "StorageControlMode": self.StorageControlMode_Read,
                }
                self._write_registers(values_to_write, unit)
                self.last_mode = None
            else:
                return

        elif power_limit <= 0:  # Limit Discharge Mode should be used.
            """
            SolarEdge discharges the battery only to SoC-Reserve.
            Disable Remote Control if SoC of battery is lower than SoC-Reserve.
            """
            registers_to_read = [
                f"Battery{battery_index}StateOfEnergy",
                "StorageControlMode",
                "StorageBackupReserved",
                "RemoteControlCommandMode",
                "RemoteControlDischargeLimit",
            ]
            try:
                values = self._read_registers(registers_to_read, unit)
            except pymodbus.exceptions.ModbusException as e:
                log.error(f"Failed to read registers: {e}")
                self.fault_state.error(f"Modbus read error: {e}")
                return
            soc = values[f"Battery{battery_index}StateOfEnergy"]
            if soc == FLOAT32_UNSUPPORTED or not 0 <= soc <= 100:
                log.warning(f"Speicher{battery_index}: Invalid SoC: {soc}")
            soc_reserve = max(int(self.min_soc + 2), int(values["StorageBackupReserved"]))
            log.debug(f"SoC-Reserve Speicher{battery_index}: {int(soc_reserve)}%.")
            discharge_limit = int(values["RemoteControlDischargeLimit"])

            if (values["StorageControlMode"] == CONTROL_MODE_REMOTE and
                values["RemoteControlCommandMode"] == REMOTE_CONTROL_COMMAND_MODE_MSC):
                # RC Discharge Mode active.
                if soc_reserve > soc:
                    # Disable Remote Control if SOC is lower than SOC-RESERVE.
                    # toDo: Problem with 2 batteries is unsolved.
                    log.debug(f"Speicher{battery_index}: Steuerung deaktivieren. SoC-Reserve unterschritten")
                    values_to_write = {
                        "RemoteControlDischargeLimit": MAX_CHARGEDISCHARGE_LIMIT,
                        "RemoteControlCommandModeDefault": REMOTE_CONTROL_COMMAND_MODE_DEFAULT,
                        "RemoteControlCommandMode": REMOTE_CONTROL_COMMAND_MODE_DEFAULT,
                        "StorageControlMode": self.StorageControlMode_Read,
                    }
                    self._write_registers(values_to_write, unit)
                    self.last_mode = None

                elif discharge_limit not in range(int(abs(power_limit)) - 10, int(abs(power_limit)) + 10):
                    # Limit only if difference is more than 10W, needed with more than 1 battery.
                    log.debug(f"Discharge-Limit Speicher{battery_index}: {int(abs(power_limit))}W.")
                    values_to_write = {
                        "RemoteControlDischargeLimit": int(min(abs(power_limit), MAX_CHARGEDISCHARGE_LIMIT))
                    }
                    self._write_registers(values_to_write, unit)
                self.last_mode = 'discharge-mode'

            else:  # Remote Control not active.
                if soc_reserve < soc:
                    # Enable Remote Control if SoC above SoC-Reserve.
                    log.debug(f"Discharge-Limit aktivieren, Speicher{battery_index}: {int(abs(power_limit))}W.")
                    self.StorageControlMode_Read = values["StorageControlMode"]
                    values_to_write = {
                        "StorageControlMode": CONTROL_MODE_REMOTE,
                        "RemoteControlCommandModeDefault": REMOTE_CONTROL_COMMAND_MODE_MSC,
                        "RemoteControlCommandMode": REMOTE_CONTROL_COMMAND_MODE_MSC,
                        "RemoteControlDischargeLimit": int(min(abs(power_limit), MAX_CHARGEDISCHARGE_LIMIT))
                    }
                    self._write_registers(values_to_write, unit)
                    self.last_mode = 'discharge-mode'

        elif power_limit > 0:  # Charge Mode should be used
            registers_to_read = [
                "StorageControlMode",
                "RemoteControlCommandMode",
                "RemoteControlChargeLimit",
            ]
            try:
                values = self._read_registers(registers_to_read, unit)
            except pymodbus.exceptions.ModbusException as e:
                log.error(f"Failed to read registers: {e}")
                self.fault_state.error(f"Modbus read error: {e}")
                return

            if (values["StorageControlMode"] == CONTROL_MODE_REMOTE and
                values["RemoteControlCommandMode"] == REMOTE_CONTROL_COMMAND_MODE_CHARGE):
                # Remote Control Charge Mode active.
                log.debug(f"Ladung Speicher{battery_index}: {int(min(abs(power_limit), MAX_CHARGEDISCHARGE_LIMIT))}W.")
                values_to_write = {
                    "RemoteControlChargeLimit": int(min(abs(power_limit), MAX_CHARGEDISCHARGE_LIMIT))
                }
                self._write_registers(values_to_write, unit)
                self.last_mode = 'charge-mode'

            else:  # Remote Control Charge Mode inactive.
                log.debug(f"Aktivierung Laden Speicher{battery_index}: {int(abs(power_limit))}W.")
                self.StorageControlMode_Read = values["StorageControlMode"]
                values_to_write = {
                    "StorageControlMode": CONTROL_MODE_REMOTE,
                    "RemoteControlCommandModeDefault": REMOTE_CONTROL_COMMAND_MODE_CHARGE,
                    "RemoteControlCommandMode": REMOTE_CONTROL_COMMAND_MODE_CHARGE,
                    "RemoteControlChargeLimit": int(min(abs(power_limit), MAX_CHARGEDISCHARGE_LIMIT))
                }
                self._write_registers(values_to_write, unit)
                self.last_mode = 'charge-mode'

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
            encoded_value = self._encode_value(value, data_type)
            try:
                self.__tcp_client.write_registers(address, encoded_value, unit=unit)
                log.debug(f"Neuer Wert {encoded_value} in Register {address} geschrieben.")
            except pymodbus.exceptions.ModbusException as e:
                log.error(f"Failed to write register {key} at address {address}: {e}")
                self.fault_state.error(f"Modbus write error: {e}")

    def _encode_value(self, value: Union[int, float], data_type: ModbusDataType) -> list:
        builder = pymodbus.payload.BinaryPayloadBuilder(
            byteorder=pymodbus.constants.Endian.Big,
            wordorder=pymodbus.constants.Endian.Little
        )
        encode_methods = {
            ModbusDataType.UINT_32: builder.add_32bit_uint,
            ModbusDataType.INT_32: builder.add_32bit_int,
            ModbusDataType.UINT_16: builder.add_16bit_uint,
            ModbusDataType.INT_16: builder.add_16bit_int,
            ModbusDataType.FLOAT_32: builder.add_32bit_float,
        }
        if data_type in encode_methods:
            if data_type == ModbusDataType.FLOAT_32:
                encode_methods[data_type](float(value))
            else:
                encode_methods[data_type](int(value))
        else:
            raise ValueError(f"Unsupported data type: {data_type}")
        return builder.to_registers()

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=SolaredgeBatSetup)
