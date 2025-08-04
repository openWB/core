#!/usr/bin/env python3
from typing import TypedDict, Any
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
# from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.chint.chint.config import CHINTCounterSetup
from pymodbus.constants import Endian


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class CHINTCounter(AbstractCounter):
    def __init__(self, component_config: CHINTCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs
        self.__modbus_id = component_config.configuration.modbus_id

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        # self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        # power = self.client.read_holding_registers(0x2012, ModbusDataType.INT_32, unit=self.__modbus_id)
        frequency = self.client.read_holding_registers(0x2044, ModbusDataType.FLOAT_32, Endian.Big, Endian.Big, unit=self.__modbus_id)/100
        # imported, exported = self.sim_counter.sim_count(power)

        try:
            power1 = self.client.read_holding_registers(0x2014, ModbusDataType.FLOAT_32, unit=self.__modbus_id) * -4
            power2 = self.client.read_holding_registers(0x2016, ModbusDataType.FLOAT_32, unit=self.__modbus_id) * -4
            power3 = self.client.read_holding_registers(0x2018, ModbusDataType.FLOAT_32, unit=self.__modbus_id) * -4
            powers = [
                power1,
                power2,
                power3]
            power = power1 + power2 + power3

            voltages = [
                self.client.read_holding_registers(0x2006, ModbusDataType.FLOAT_32, unit=self.__modbus_id) / 10,
                self.client.read_holding_registers(0x2008, ModbusDataType.FLOAT_32, unit=self.__modbus_id) / 10,
                self.client.read_holding_registers(0x200A, ModbusDataType.FLOAT_32, unit=self.__modbus_id) / 10
            ]

            currents = [
                self.client.read_holding_registers(0x200C, ModbusDataType.FLOAT_32, unit=self.__modbus_id) / 10,
                self.client.read_holding_registers(0x200E, ModbusDataType.FLOAT_32, unit=self.__modbus_id) / 10,
                self.client.read_holding_registers(0x2010, ModbusDataType.FLOAT_32, unit=self.__modbus_id) / 10
            ]
        except Exception:
            powers = None

        counter_state = CounterState(
            currents=currents,
            # imported=imported,
            # exported=exported,
            power=power,
            frequency=frequency,
            # power_factors=power_factors,
            powers=powers,
            voltages=voltages
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=CHINTCounterSetup)
