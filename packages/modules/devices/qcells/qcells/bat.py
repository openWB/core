#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_component_value_store
from modules.devices.qcells.qcells.config import QCellsBatSetup


class KwargsDict(TypedDict):
    modbus_id: int
    client: ModbusTcpClient_


class QCellsBat(AbstractBat):
    def __init__(self, component_config: QCellsBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        power = self.client.read_input_registers(0x0016, ModbusDataType.INT_16, unit=self.__modbus_id)
        soc = self.client.read_input_registers(0x001C, ModbusDataType.UINT_16, unit=self.__modbus_id)
        imported = self.client.read_input_registers(
            0x0021, ModbusDataType.UINT_16, unit=self.__modbus_id) * 100
        exported = self.client.read_input_registers(
            0x001D, ModbusDataType.UINT_16, unit=self.__modbus_id) * 100

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=QCellsBatSetup)
