#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.upower.upower.config import UPowerCounterSetup
from modules.devices.upower.upower.version import UPowerVersion


class UPowerCounter(AbstractCounter):
    def __init__(self,
                 component_config: Union[Dict, UPowerCounterSetup],
                 version: UPowerVersion,
                 modbus_id: int) -> None:
        self.component_config = dataclass_from_dict(UPowerCounterSetup, component_config)
        self.__modbus_id = modbus_id
        self.version = version
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")

    def update(self, client: ModbusTcpClient_):
        if self.version == UPowerVersion.GEN_1:
            power = client.read_holding_registers(1000, ModbusDataType.INT_32, unit=self.__modbus_id) * -1
            frequency = client.read_holding_registers(11015, ModbusDataType.UINT_16, unit=self.__modbus_id)

            powers = [-value for value in client.read_holding_registers(
                10994, [ModbusDataType.INT_32] * 3, unit=self.__modbus_id)]
            exported = client.read_holding_registers(31102, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100
            imported = client.read_holding_registers(31104, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100
        else:
            power = client.read_holding_registers(1219, ModbusDataType.INT_16, unit=self.__modbus_id) * -10
            frequency = client.read_holding_registers(
                1759, ModbusDataType.UINT_16, unit=self.__modbus_id) / 100

            powers = [-10 * value for value in client.read_holding_registers(
                1750, [ModbusDataType.INT_16] * 3, unit=self.__modbus_id
            )]
            imported, exported = self.sim_counter.sim_count(power)

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            powers=powers,
            frequency=frequency
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=UPowerCounterSetup)
