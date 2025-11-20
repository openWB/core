#!/usr/bin/env python3
import logging
from typing import TypedDict, Any
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_counter_value_store
from modules.devices.chint.chint.config import CHINTCounterSetup

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    client: ModbusTcpClient_


class CHINTCounter(AbstractCounter):
    def __init__(self, component_config: CHINTCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.__modbus_id = self.component_config.configuration.modbus_id

    def update(self):
        powers = voltages = currents = power_factors = None
        imported_ep = exported_ep = power = frequency = 0
        irat = self.client.read_holding_registers(0x0006, ModbusDataType.INT_16, device_id=self.__modbus_id)
        urat = self.client.read_holding_registers(0x0007, ModbusDataType.INT_16, device_id=self.__modbus_id)
        power_ratio = urat*0.1*irat*0.1

        frequency = self.client.read_holding_registers(0x2044, ModbusDataType.FLOAT_32, device_id=self.__modbus_id)/100
        power = self.client.read_holding_registers(0x2012,
                                                   ModbusDataType.FLOAT_32, device_id=self.__modbus_id) * power_ratio
        powers = [self.client.read_holding_registers(reg, ModbusDataType.FLOAT_32, device_id=self.__modbus_id) * power_ratio
                  for reg in [0x2014, 0x2016, 0x2018]]
        voltage_ratio = urat*0.1*0.1
        voltages = [self.client.read_holding_registers(
            reg, ModbusDataType.FLOAT_32, device_id=self.__modbus_id) * voltage_ratio
            for reg in [0x2006, 0x2008, 0x200A]]
        current_ratio = irat*0.001
        currents = [self.client.read_holding_registers(
            reg, ModbusDataType.FLOAT_32, device_id=self.__modbus_id) * current_ratio
            for reg in [0x200C, 0x200E, 0x2010]]
        power_factors = [self.client.read_holding_registers(reg, ModbusDataType.FLOAT_32, device_id=self.__modbus_id) * 0.001
                         for reg in [0x202C, 0x202E, 0x2030]]
        ep_ratio = irat * urat * 100
        imported_ep = self.client.read_holding_registers(0x401E,
                                                         ModbusDataType.FLOAT_32, device_id=self.__modbus_id) * ep_ratio
        exported_ep = self.client.read_holding_registers(0x4028,
                                                         ModbusDataType.FLOAT_32, device_id=self.__modbus_id) * ep_ratio

        counter_state = CounterState(
            currents=currents,
            imported=imported_ep,
            exported=exported_ep,
            power=power,
            frequency=frequency,
            power_factors=power_factors,
            powers=powers,
            voltages=voltages
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=CHINTCounterSetup)
