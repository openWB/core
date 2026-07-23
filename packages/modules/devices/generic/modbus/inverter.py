#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.utils.peak_filter import PeakFilter
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store._inverter import get_inverter_value_store
from modules.devices.generic.modbus.config import GenericModbusInverterSetup
from modules.common.component_type import ComponentType
from modules.common.simcount import SimCounter

from modules.devices.generic.modbus.helper import check_data


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class GenericModbusInverter(AbstractInverter):
    def __init__(self, component_config: GenericModbusInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.INVERTER, self.component_config.id, self.fault_state)
        self.sim_counter = SimCounter(self.kwargs['device_id'], self.component_config.id, self.component_config.type)

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
                    int(self.component_config.configuration.current_L1.reg_address), ModbusDataType[
                        self.component_config.configuration.current_L1.reg_type],
                    byteorder=self.component_config.configuration.current_L1.byteorder,
                    wordorder=self.component_config.configuration.current_L1.wordorder, unit=unit)

            if self.component_config.configuration.current_L2.reg_address is not None:
                check_data(self.component_config.configuration.current_L2)
                currents[1] = self.client.read_input_registers(
                    int(self.component_config.configuration.current_L2.reg_address), ModbusDataType[
                        self.component_config.configuration.current_L2.reg_type],
                    byteorder=self.component_config.configuration.current_L2.byteorder,
                    wordorder=self.component_config.configuration.current_L2.wordorder, unit=unit)

            if self.component_config.configuration.current_L3.reg_address is not None:
                check_data(self.component_config.configuration.current_L3)
                currents[2] = self.client.read_input_registers(
                    int(self.component_config.configuration.current_L3.reg_address), ModbusDataType[
                        self.component_config.configuration.current_L3.reg_type],
                    byteorder=self.component_config.configuration.current_L3.byteorder,
                    wordorder=self.component_config.configuration.current_L3.wordorder, unit=unit)

        # DC Power
        #
        if self.component_config.configuration.dc_power.reg_address is not None:
            check_data(self.component_config.configuration.dc_power)
            dc_power = self.client.read_input_registers(
                int(self.component_config.configuration.dc_power.reg_address), ModbusDataType[
                    self.component_config.configuration.dc_power.reg_type],
                byteorder=self.component_config.configuration.dc_power.byteorder,
                wordorder=self.component_config.configuration.dc_power.wordorder, unit=unit)

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

        inverter_state = InverterState(
            power=power,
            exported=exported,
            imported=imported,
        )

        if "dc_power" in locals():
            inverter_state.dc_power = dc_power
        if "currents" in locals():
            inverter_state.currents = currents
        if 'serial_number' in locals():
            inverter_state.serial_number = serial_number

        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=GenericModbusInverterSetup)
