#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_inverter_value_store
from modules.devices.growatt.growatt.config import GrowattInverterSetup
from modules.devices.growatt.growatt.version import GrowattVersion


class GrowattInverter(AbstractInverter):
    def __init__(self,
                 component_config: Union[Dict, GrowattInverterSetup],
                 modbus_id: int,
                 version: GrowattVersion) -> None:
        self.component_config = dataclass_from_dict(GrowattInverterSetup, component_config)
        self.__modbus_id = modbus_id
        self.version = version
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, client: ModbusTcpClient_) -> None:
        if self.version == GrowattVersion.max_series:
            power = client.read_input_registers(
                1, ModbusDataType.UINT_32, unit=self.__modbus_id) / -10
            exported = client.read_input_registers(
                91, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100
        else:
            power = client.read_input_registers(
                3001, ModbusDataType.UINT_32, unit=self.__modbus_id) / -10
            exported = client.read_input_registers(
                3053, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100

        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=GrowattInverterSetup)
