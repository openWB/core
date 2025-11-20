#!/usr/bin/env python3
from typing import TypedDict, Any
from pymodbus.constants import Endian

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_inverter_value_store
from modules.devices.qcells.qcells.config import QCellsInverterSetup


class KwargsDict(TypedDict):
    modbus_id: int
    client: ModbusTcpClient_


class QCellsInverter(AbstractInverter):
    def __init__(self, component_config: QCellsInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        power_string1 = (self.client.read_input_registers(
            0x0003, ModbusDataType.INT_16, device_id=self.__modbus_id) / 10) * \
            (self.client.read_input_registers(0x0005, ModbusDataType.INT_16, device_id=self.__modbus_id) / 10)
        power_string2 = (self.client.read_input_registers(
            0x0004, ModbusDataType.INT_16, device_id=self.__modbus_id) / 10) * \
            (self.client.read_input_registers(0x0006, ModbusDataType.INT_16, device_id=self.__modbus_id) / 10)
        power = (power_string1 + power_string2) * -1
        exported = self.client.read_input_registers(0x0094, ModbusDataType.UINT_32, wordorder=Endian.Little,
                                                    device_id=self.__modbus_id) * 100

        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=QCellsInverterSetup)
