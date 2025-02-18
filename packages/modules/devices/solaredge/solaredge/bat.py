#!/usr/bin/env python3
"""
This script provides control for the SolarEdge battery system via Modbus.
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
    ADVANCED_PWR_CTRL_REGISTER = 57740  # INT_16
    COMMIT_REGISTER = 57741  # INT_16
    SOC_REGISTER = 57732  # FLOAT_32
    POWER_REGISTER = 57716  # FLOAT_32
    DISCHARGE_LIMIT_REGISTER = 57360  # FLOAT_32
    REMOTE_CONTROL_REGISTER = 57348  # INT_16, must be 4

    def __init__(
        self,
        device_id: int,
        component_config: Union[Dict, SolaredgeBatSetup],
        tcp_client: modbus.ModbusTcpClient_,
    ) -> None:
        self._device_id = device_id
        self.component_config = dataclass_from_dict(SolaredgeBatSetup, component_config)
        self.__tcp_client = tcp_client
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="storage")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        try:
            state = self.read_state()
            self.store.set(state)
        except Exception as e:
            log.error(f"Error updating battery state: {e}")
        log.info("Battery state updated.")

    def read_state(self) -> BatState:
        power, soc = self.get_values()
        if soc is None or power is None:
            log.error("Invalid values read from Modbus registers.")
            return BatState(power=0, soc=0, imported=0, exported=0)
        imported, exported = self.sim_counter.sim_count(power)
        log.debug(f"Read - Power: {power}, SOC: {soc}")
        return BatState(power=power, soc=soc, imported=imported, exported=exported)

    def ensure_remote_control_mode(self, unit: int) -> bool:
        try:
            current_mode = self.__tcp_client.read_holding_registers(
                self.REMOTE_CONTROL_REGISTER, ModbusDataType.INT_16, unit=unit
            )
            if isinstance(current_mode, list) and current_mode and current_mode[0] == 4:
                log.debug("Remote control mode is already enabled.")
                return True

            log.info("Enabling remote control mode.")
            def create_payload_builder():
        return modbus.BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Little)

    builder = create_payload_builder()
            builder.add_16bit_int(4)
            self.__tcp_client.write_registers(self.REMOTE_CONTROL_REGISTER, builder.to_registers(), unit=unit)
            self.commit_changes(unit)
            return True
        except Exception as e:
            log.error(f"Error enabling remote control mode: {e}")
            return False

    def ensure_advanced_power_control(self, unit: int) -> bool:
        if not self.ensure_remote_control_mode(unit):
            return False
        try:
            current_state = self.__tcp_client.read_holding_registers(
                self.ADVANCED_PWR_CTRL_REGISTER, ModbusDataType.INT_16, unit=unit
            )
            if current_state and current_state[0] == 1:
                log.debug("Advanced power control is already enabled.")
                return True
            log.error("Advanced power control is not enabled. Please enable it.")
            return False
        except Exception as e:
            log.error(f"Error checking advanced power control: {e}")
            return False

    def activate_advanced_power_control(self, unit: int) -> None:
        if not self.ensure_remote_control_mode(unit):
            return
        try:
            builder = modbus.BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Little)
            builder.add_16bit_int(1)
            self.__tcp_client.write_registers(self.ADVANCED_PWR_CTRL_REGISTER, builder.to_registers(), unit=unit)
            log.debug("Advanced power control successfully activated.")
            self.commit_changes(unit)
        except Exception as e:
            log.error(f"Error activating advanced power control: {e}")

    def commit_changes(self, unit: int) -> None:
        try:
            builder = modbus.BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Little)
            builder.add_16bit_int(1)
            self.__tcp_client.write_registers(self.COMMIT_REGISTER, builder.to_registers(), unit=unit)
            log.debug("Changes successfully committed.")
        except Exception as e:
            log.error(f"Error committing changes: {e}")

    def set_power_limit(self, power_limit: Optional[Union[int, float]]) -> None:
        unit = self.component_config.configuration.modbus_id
        if not self.ensure_advanced_power_control(unit):
            self.activate_advanced_power_control(unit)

        power_limit = 5000 if power_limit is None else power_limit

        if power_limit < 0 or power_limit > 5000:
            log.error(f"Invalid discharge limit: {power_limit}. Must be between 0 and 5000.")
            return

        try:
            current_limit = self.__tcp_client.read_holding_registers(
                self.DISCHARGE_LIMIT_REGISTER, ModbusDataType.FLOAT_32, unit=unit
            )
            if current_limit and current_limit[0] == power_limit:
                log.info(f"Discharge limit is already set to {power_limit} W. No action required.")
                return

            builder = modbus.BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Little)
            builder.add_32bit_float(float(power_limit))
            if current_limit and current_limit[0] != power_limit:
                self.__tcp_client.write_registers(self.DISCHARGE_LIMIT_REGISTER, builder.to_registers(), unit=unit)
            log.debug(f"Discharge limit successfully set to {power_limit} W.")
        except Exception as e:
            log.error(f"Error setting discharge limit: {e}")


component_descriptor = ComponentDescriptor(configuration_factory=SolaredgeBatSetup)
