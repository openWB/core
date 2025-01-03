#!/usr/bin/env python3
"""
This script provides control for the SolarEdge battery system via Modbus.

Features:
- Reading battery state of charge (SOC) and power.
- Enabling advanced power control with confirmation.
- Setting power limits, including blocking battery usage.

Functions are designed to minimize unnecessary Modbus writes and ensure robust control.
"""

import logging
from typing import Dict, Tuple, Union, Optional

from pymodbus.constants import Endian

from dataclass_utils import dataclass_from_dict
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


class SolaredgeBat(AbstractBat):
    ADVANCED_PWR_CTRL_REGISTER = 57740  # Register for advanced power control
    COMMIT_REGISTER = 57741  # Register to commit changes

    def __init__(self,
                 device_id: int,
                 component_config: Union[Dict, SolaredgeBatSetup],
                 tcp_client: modbus.ModbusTcpClient_) -> None:
        """
        Initialize the SolarEdge battery control class.

        Args:
            device_id (int): The device ID of the battery.
            component_config (Union[Dict, SolaredgeBatSetup]): Configuration data for the battery.
            tcp_client (modbus.ModbusTcpClient_): Modbus TCP client for communication.
        """
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(SolaredgeBatSetup, component_config)
        self.__tcp_client = tcp_client
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="storage")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        """
        Update the stored battery state by reading current values.
        """
        self.store.set(self.read_state())

    def read_state(self) -> BatState:
        """
        Read the current state of the battery, including power and SOC.

        Returns:
            BatState: A dataclass containing power, SOC, imported, and exported energy values.
        """
        power, soc = self.get_values()
        if soc is None or power is None:
            log.error("Invalid values read from Modbus registers.")
            return BatState(power=0, soc=0, imported=0, exported=0)
        imported, exported = self.sim_counter.sim_count(power)
        log.debug(f"Read - Power: {power}, SOC: {soc}")
        return BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )

    def get_values(self) -> Tuple[Optional[float], Optional[float]]:
        """
        Fetch the current SOC and power from Modbus registers.

        Returns:
            Tuple[Optional[float], Optional[float]]: SOC and power values, or None if an error occurs.
        """
        unit = self.component_config.configuration.modbus_id
        try:
            soc = self.__tcp_client.read_holding_registers(
                57732, ModbusDataType.FLOAT_32, wordorder=Endian.Little, unit=unit)  # SOC Register
            power = self.__tcp_client.read_holding_registers(
                57716, ModbusDataType.FLOAT_32, wordorder=Endian.Little, unit=unit)  # Power Register
            return power, soc
        except Exception as e:
            log.error(f"Error reading from Modbus registers: {e} - Register: 57732, Unit: {unit}")
            return None, None

    def ensure_advanced_power_control(self, unit: int) -> bool:
        """
        Ensure that advanced power control is enabled.

        Args:
            unit (int): Modbus unit ID.

        Returns:
            bool: True if advanced power control is enabled, False otherwise.
        """
        try:
            current_state = self.__tcp_client.read_holding_registers(
                self.ADVANCED_PWR_CTRL_REGISTER, ModbusDataType.FLOAT_32, unit=unit
            )
            if current_state != 1.0:
                log.error("Advanced power control is not enabled. Please enable it.")
                return False
            log.debug("Advanced power control is already enabled.")
            return True
        except Exception as e:
            log.error(f"Error checking advanced power control: {e}")
            return False

    def activate_advanced_power_control(self, unit: int) -> None:
        """
        Activate advanced power control by writing to the appropriate register.

        Args:
            unit (int): Modbus unit ID.
        """
        try:
            builder = modbus.BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Little)
            builder.add_32bit_float(1.0)  # Activate advanced power control
            self.__tcp_client.write_registers(
                self.ADVANCED_PWR_CTRL_REGISTER, builder.to_registers(), unit=unit
            )
            log.debug("Advanced power control successfully activated.")

            # Confirm changes
            self.commit_changes(unit)
        except Exception as e:
            log.error(f"Error activating advanced power control: {e}")

    def commit_changes(self, unit: int) -> None:
        """
        Commit changes to finalize advanced power control activation.

        Args:
            unit (int): Modbus unit ID.
        """
        try:
            builder = modbus.BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Little)
            builder.add_32bit_float(1.0)  # Commit changes
            self.__tcp_client.write_registers(
                self.COMMIT_REGISTER, builder.to_registers(), unit=unit
            )
            log.debug("Changes successfully committed.")
        except Exception as e:
            log.error(f"Error committing changes: {e}")

    def set_power_limit(self, power_limit: Union[Optional[int], str]) -> None:
        """
        Set the power limit for the battery. Supports three modes:
        - Default limit (5000 W)
        - Specific wattage limit
        - Blocked mode (set limit to 0 W)

        Args:
            power_limit (Union[Optional[int], str]): Power limit value, None, or "blocked".
        """
        DISCHARGE_LIMIT_REGISTER = 57360  # Discharge Limit Register
        unit = self.component_config.configuration.modbus_id

        # Ensure advanced power control is enabled
        if not self.ensure_advanced_power_control(unit):
            self.activate_advanced_power_control(unit)

        # Logic for None (default limit)
        if power_limit is None:
            log.debug("Zero-point regulation activated, discharge limit set to 5000 W.")
            power_limit = 5000  # Maximum discharge power

        # Logic for 'blocked' (disable battery usage)
        elif isinstance(power_limit, str) and power_limit.lower() == 'blocked':
            log.debug("Battery usage blocked, discharge limit set to 0 W.")
            power_limit = 0

        # Validate input values
        elif isinstance(power_limit, int) and (power_limit < 0 or power_limit > 5000):
            log.error(f"Invalid discharge limit: {power_limit}. Must be between 0 and 5000.")
            return

        try:
            # Read current limit
            current_limit = self.__tcp_client.read_holding_registers(
                DISCHARGE_LIMIT_REGISTER, ModbusDataType.FLOAT_32, unit=unit)

            # Only write if the new value differs from the existing one
            if current_limit != power_limit:
                self.__tcp_client.write_registers(
                    DISCHARGE_LIMIT_REGISTER, [float_32(power_limit)], unit=unit)
                log.debug(f"Discharge limit successfully set to {power_limit} W.")
            else:
                log.info(f"Discharge limit is already set to {current_limit} W. No action required.")
        except Exception as e:
            log.error(f"Error setting discharge limit: {e}")

component_descriptor = ComponentDescriptor(configuration_factory=SolaredgeBatSetup)
