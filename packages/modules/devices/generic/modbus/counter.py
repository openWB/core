#!/usr/bin/env python3
from typing import Any, TypedDict
from modules.devices.generic.modbus.helper import check_data
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.component_type import ComponentDescriptor
from modules.common.simcount._simcounter import SimCounter
from modules.devices.generic.modbus.config import GenericModbusCounterSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType

from modules.common.store import get_counter_value_store

from modules.common.modbus import ModbusDataType, ModbusTcpClient_

import logging
log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class GenericModbusCounter(AbstractCounter):
    def __init__(self, component_config: GenericModbusCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.COUNTER, self.component_config.id, self.fault_state)

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id

        # Power
        #
        if self.component_config.configuration.power.reg_address is not None:
            check_data(self.component_config.configuration.power)
            power = self.client.read_input_registers(
                int(self.component_config.configuration.power.reg_address), ModbusDataType[
                    self.component_config.configuration.power.reg_type],
                byteorder=self.component_config.configuration.power.byteorder,
                wordorder=self.component_config.configuration.power.wordorder, unit=unit)
        else:
            raise ValueError("Leistungsregister muss angegeben werden.")

        # Voltages
        #
        if (self.component_config.configuration.voltage_L1.reg_address is not None or
            self.component_config.configuration.voltage_L2.reg_address is not None or
                self.component_config.configuration.voltage_L3.reg_address is not None):
            # Kein register angegeben
            voltages = [0.0]*3
            if self.component_config.configuration.voltage_L1.reg_address is not None:
                check_data(self.component_config.configuration.voltage_L1)
                voltages[0] = self.client.read_input_registers(
                    int(self.component_config.configuration.voltage_L1.reg_address),
                    ModbusDataType[self.component_config.configuration.voltage_L1.reg_type],
                    byteorder=self.component_config.configuration.voltage_L1.byteorder,
                    wordorder=self.component_config.configuration.voltage_L1.wordorder, unit=unit)

            if self.component_config.configuration.voltage_L2.reg_address is not None:
                check_data(self.component_config.configuration.voltage_L2)
                voltages[1] = self.client.read_input_registers(
                    int(self.component_config.configuration.voltage_L2.reg_address),
                    ModbusDataType[self.component_config.configuration.voltage_L2.reg_type],
                    byteorder=self.component_config.configuration.voltage_L2.byteorder,
                    wordorder=self.component_config.configuration.voltage_L2.wordorder, unit=unit)

            if self.component_config.configuration.voltage_L3.reg_address is not None:
                check_data(self.component_config.configuration.voltage_L3)
                voltages[2] = self.client.read_input_registers(
                    int(self.component_config.configuration.voltage_L3.reg_address),
                    ModbusDataType[self.component_config.configuration.voltage_L3.reg_type],
                    byteorder=self.component_config.configuration.voltage_L3.byteorder,
                    wordorder=self.component_config.configuration.voltage_L3.wordorder, unit=unit)

        # Currents
        #
        if (self.component_config.configuration.current_L1.reg_address is not None or
            self.component_config.configuration.current_L2.reg_address is not None or
                self.component_config.configuration.current_L3.reg_address is not None):
            # mind. ein register angegeben
            currents = [0.0]*3
            if self.component_config.configuration.current_L1.reg_address is not None:
                check_data(self.component_config.configuration.current_L1)
                currents[0] = self.client.read_input_registers(
                    int(self.component_config.configuration.current_L1.reg_address),
                    ModbusDataType[self.component_config.configuration.current_L1.reg_type],
                    byteorder=self.component_config.configuration.current_L1.byteorder,
                    wordorder=self.component_config.configuration.current_L1.wordorder, unit=unit)

            if self.component_config.configuration.current_L2.reg_address is not None:
                check_data(self.component_config.configuration.current_L2)
                currents[1] = self.client.read_input_registers(
                    int(self.component_config.configuration.current_L2.reg_address),
                    ModbusDataType[self.component_config.configuration.current_L2.reg_type],
                    byteorder=self.component_config.configuration.current_L2.byteorder,
                    wordorder=self.component_config.configuration.current_L2.wordorder, unit=unit)

            if self.component_config.configuration.current_L3.reg_address is not None:
                check_data(self.component_config.configuration.current_L3)
                currents[2] = self.client.read_input_registers(
                    int(self.component_config.configuration.current_L3.reg_address),
                    ModbusDataType[self.component_config.configuration.current_L3.reg_type],
                    byteorder=self.component_config.configuration.current_L3.byteorder,
                    wordorder=self.component_config.configuration.current_L3.wordorder, unit=unit)

        # Powers
        #
        if (self.component_config.configuration.powers_L1.reg_address is not None or
            self.component_config.configuration.powers_L2.reg_address is not None or
                self.component_config.configuration.powers_L3.reg_address is not None):
            # mind. ein register angegeben
            powers = [0.0]*3
            if self.component_config.configuration.powers_L1.reg_address is not None:
                check_data(self.component_config.configuration.powers_L1)
                powers[0] = self.client.read_input_registers(
                    int(self.component_config.configuration.powers_L1.reg_address),
                    ModbusDataType[self.component_config.configuration.powers_L1.reg_type],
                    byteorder=self.component_config.configuration.powers_L1.byteorder,
                    wordorder=self.component_config.configuration.powers_L1.wordorder, unit=unit)

            if self.component_config.configuration.powers_L2.reg_address is not None:
                check_data(self.component_config.configuration.powers_L2)
                powers[1] = self.client.read_input_registers(
                    int(self.component_config.configuration.powers_L2.reg_address),
                    ModbusDataType[self.component_config.configuration.powers_L2.reg_type],
                    byteorder=self.component_config.configuration.powers_L2.byteorder,
                    wordorder=self.component_config.configuration.powers_L2.wordorder, unit=unit)

            if self.component_config.configuration.powers_L3.reg_address is not None:
                check_data(self.component_config.configuration.powers_L3)
                powers[2] = self.client.read_input_registers(
                    int(self.component_config.configuration.powers_L3.reg_address),
                    ModbusDataType[self.component_config.configuration.powers_L3.reg_type],
                    byteorder=self.component_config.configuration.powers_L3.byteorder,
                    wordorder=self.component_config.configuration.powers_L3.wordorder, unit=unit)

        # Power Factors‚
        #
        if (self.component_config.configuration.power_factor_L1.reg_address is not None or
            self.component_config.configuration.power_factor_L2.reg_address is not None or
                self.component_config.configuration.power_factor_L3.reg_address is not None):
            # mind. ein register angegeben
            power_factors = [0.0]*3
            if self.component_config.configuration.power_factor_L1.reg_address is not None:
                check_data(self.component_config.configuration.power_factor_L1)
                power_factors[0] = self.client.read_input_registers(
                    int(self.component_config.configuration.power_factor_L1.reg_address),
                    ModbusDataType[self.component_config.configuration.power_factor_L1.reg_type],
                    byteorder=self.component_config.configuration.power_factor_L1.byteorder,
                    wordorder=self.component_config.configuration.power_factor_L1.wordorder, unit=unit)

            if self.component_config.configuration.power_factor_L2.reg_address is not None:
                check_data(self.component_config.configuration.power_factor_L2)
                power_factors[1] = self.client.read_input_registers(
                    int(self.component_config.configuration.power_factor_L2.reg_address),
                    ModbusDataType[self.component_config.configuration.power_factor_L2.reg_type],
                    byteorder=self.component_config.configuration.power_factor_L2.byteorder,
                    wordorder=self.component_config.configuration.power_factor_L2.wordorder, unit=unit)

            if self.component_config.configuration.power_factor_L3.reg_address is not None:
                check_data(self.component_config.configuration.power_factor_L3)
                power_factors[2] = self.client.read_input_registers(
                    int(self.component_config.configuration.power_factor_L3.reg_address),
                    ModbusDataType[self.component_config.configuration.power_factor_L3.reg_type],
                    byteorder=self.component_config.configuration.power_factor_L3.byteorder,
                    wordorder=self.component_config.configuration.power_factor_L3.wordorder, unit=unit)

        # Frequency
        #
        if self.component_config.configuration.frequency.reg_address is not None:
            check_data(self.component_config.configuration.frequency)
            frequency = self.client.read_input_registers(
                int(self.component_config.configuration.frequency.reg_address), ModbusDataType[
                    self.component_config.configuration.frequency.reg_type],
                byteorder=self.component_config.configuration.frequency.byteorder,
                wordorder=self.component_config.configuration.frequency.wordorder, unit=unit)

        # Imported
        #
        if self.component_config.configuration.imported.reg_address is not None:
            check_data(self.component_config.configuration.imported)
            imported = self.client.read_input_registers(
                int(self.component_config.configuration.imported.reg_address), ModbusDataType[
                    self.component_config.configuration.imported.reg_type],
                byteorder=self.component_config.configuration.imported.byteorder,
                wordorder=self.component_config.configuration.imported.wordorder, unit=unit)
        else:
            imported = None

        # Exported
        #
        if self.component_config.configuration.exported.reg_address is not None:
            check_data(self.component_config.configuration.exported)
            exported = self.client.read_input_registers(
                int(self.component_config.configuration.exported.reg_address), ModbusDataType[
                    self.component_config.configuration.exported.reg_type],
                byteorder=self.component_config.configuration.exported.byteorder,
                wordorder=self.component_config.configuration.exported.wordorder, unit=unit)
        else:
            exported = None

        # Serial Number
        #
        if self.component_config.configuration.serial_number.reg_address is not None:
            check_data(self.component_config.configuration.serial_number)
            serial_number = self.client.read_input_registers(
                int(self.component_config.configuration.serial_number.reg_address), ModbusDataType[
                    self.component_config.configuration.serial_number.reg_type],
                byteorder=self.component_config.configuration.serial_number.byteorder,
                wordorder=self.component_config.configuration.serial_number.wordorder, unit=unit)

        if power is not None:
            self.peak_filter.check_values(power)
            if imported is None or exported is None:
                imported, exported = self.sim_counter.sim_count(power)
            imported, exported = self.peak_filter.check_values(power, imported, exported)

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power
        )

        if "voltages" in locals():
            counter_state.voltages = voltages
        if "currents" in locals():
            counter_state.currents = currents
        if 'powers' in locals():
            counter_state.powers = powers
        if "power_factors" in locals():
            counter_state.power_factors = power_factors
        if 'frequency' in locals():
            counter_state.frequency = frequency
        if 'serial_number' in locals():
            counter_state.serial_number = serial_number

        self.store.set(counter_state)

        log.debug(f"CounterState updated: {counter_state}")


component_descriptor = ComponentDescriptor(configuration_factory=GenericModbusCounterSetup)
