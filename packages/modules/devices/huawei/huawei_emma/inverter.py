#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.huawei.huawei_emma.config import Huawei_EmmaInverterSetup


class KwargsDict(TypedDict):
    device_id: int
    modbus_id: int
    client: ModbusTcpClient_


class Huawei_EmmaInverter(AbstractInverter):
    def __init__(self, component_config: Huawei_EmmaInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.modbus_id: int = self.kwargs['modbus_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        power = self.client.read_holding_registers(30354, ModbusDataType.INT_32, unit=self.modbus_id) * -1
        exported = self.client.read_holding_registers(30348, ModbusDataType.UINT_64, unit=self.modbus_id) * 10

        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=Huawei_EmmaInverterSetup)
