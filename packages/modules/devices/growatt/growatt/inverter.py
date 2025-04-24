#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_inverter_value_store
from modules.devices.growatt.growatt.config import GrowattInverterSetup
from modules.devices.growatt.growatt.version import GrowattVersion


class KwargsDict(TypedDict):
    modbus_id: int
    version: GrowattVersion
    client: ModbusTcpClient_


class GrowattInverter(AbstractInverter):
    def __init__(self, component_config: GrowattInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.version: GrowattVersion = self.kwargs['version']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        if self.version == GrowattVersion.max_series:
            power = self.client.read_input_registers(
                1, ModbusDataType.UINT_32, unit=self.__modbus_id) / -10
            exported = self.client.read_input_registers(
                91, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100
        else:
            power = self.client.read_input_registers(
                3001, ModbusDataType.UINT_32, unit=self.__modbus_id) / -10
            exported = self.client.read_input_registers(
                3053, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100

        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=GrowattInverterSetup)
