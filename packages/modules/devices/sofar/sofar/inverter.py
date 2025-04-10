#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_inverter_value_store
from modules.devices.sofar.sofar.config import SofarInverterSetup


class KwargsDict(TypedDict):
    client: ModbusTcpClient_
    modbus_id: int


class SofarInverter(AbstractInverter):
    def __init__(self, component_config: SofarInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, client: ModbusTcpClient_) -> None:
        # 0x05C4 Power_PV_Total UINT16 in kW accuracy 0,1
        power = self.client.read_holding_registers(0x05C4, ModbusDataType.UINT_16, unit=self.__modbus_id) * -100
        exported = self.client.read_holding_registers(0x0686, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100

        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SofarInverterSetup)
