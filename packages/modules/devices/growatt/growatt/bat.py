#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_bat_value_store
from modules.devices.growatt.growatt.config import GrowattBatSetup
from modules.devices.growatt.growatt.version import GrowattVersion


class KwargsDict(TypedDict):
    modbus_id: int
    version: GrowattVersion
    client: ModbusTcpClient_


class GrowattBat(AbstractBat):
    def __init__(self, component_config: GrowattBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.version: GrowattVersion = self.kwargs['version']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        if self.version == GrowattVersion.max_series:
            power_in = self.client.read_input_registers(
                1011, ModbusDataType.UINT_32, unit=self.__modbus_id) * 0.1
            power_out = self.client.read_input_registers(
                1009, ModbusDataType.UINT_32, unit=self.__modbus_id) * -0.1
            power = power_in + power_out

            soc = self.client.read_input_registers(1014, ModbusDataType.UINT_16, unit=self.__modbus_id)
            imported = self.client.read_input_registers(
                1058, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100
            exported = self.client.read_input_registers(
                1054, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100
        else:
            power_in = self.client.read_input_registers(
                3180, ModbusDataType.UINT_32, unit=self.__modbus_id) * -0.1
            power_out = self.client.read_input_registers(
                3178, ModbusDataType.UINT_32, unit=self.__modbus_id) * 0.1
            power = power_in + power_out

            soc = self.client.read_input_registers(3171, ModbusDataType.UINT_16, unit=self.__modbus_id)
            imported = self.client.read_input_registers(
                3131, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100
            exported = self.client.read_input_registers(
                3127, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=GrowattBatSetup)
