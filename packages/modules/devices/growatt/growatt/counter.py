#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_counter_value_store
from modules.devices.growatt.growatt.config import GrowattCounterSetup
from modules.devices.growatt.growatt.version import GrowattVersion


class KwargsDict(TypedDict):
    modbus_id: int
    version: GrowattVersion
    client: ModbusTcpClient_


class GrowattCounter(AbstractCounter):
    def __init__(self, component_config: GrowattCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.version: GrowattVersion = self.kwargs['version']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        if self.version == GrowattVersion.max_series:
            power_in = self.client.read_input_registers(1021, ModbusDataType.UINT_32, unit=self.__modbus_id) * 0.1
            power_out = self.client.read_input_registers(1029, ModbusDataType.UINT_32, unit=self.__modbus_id) * -0.1
            power = power_in + power_out

            powers = [
                self.client.read_input_registers(
                    40, ModbusDataType.INT_32, unit=self.__modbus_id) / 10,
                self.client.read_input_registers(
                    44, ModbusDataType.INT_32, unit=self.__modbus_id) / 10,
                self.client.read_input_registers(
                    48, ModbusDataType.INT_32, unit=self.__modbus_id) / 10]

            # Einheit 0.1 kWh
            exported = self.client.read_input_registers(1050, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100
            imported = self.client.read_input_registers(1046, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100

        # TL-X Dokumentation hat die gleichen Register wie die MAX Serie,
        # zusätzlich sind aber auch unten abweichende enthalten
        else:
            power_in = self.client.read_input_registers(3041, ModbusDataType.UINT_32, unit=self.__modbus_id) * 0.1
            power_out = self.client.read_input_registers(3043, ModbusDataType.UINT_32, unit=self.__modbus_id) * -0.1
            power = power_in + power_out

            powers = [
                self.client.read_input_registers(
                    3028, ModbusDataType.INT_32, unit=self.__modbus_id) / 10,
                self.client.read_input_registers(
                    3032, ModbusDataType.INT_32, unit=self.__modbus_id) / 10,
                self.client.read_input_registers(
                    3036, ModbusDataType.INT_32, unit=self.__modbus_id) / 10]

            # Einheit 0.1 kWh
            exported = self.client.read_input_registers(3073, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100
            imported = self.client.read_input_registers(3069, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            powers=powers
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=GrowattCounterSetup)
