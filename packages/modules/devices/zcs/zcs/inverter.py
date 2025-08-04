#!/usr/bin/env python3
from typing import TypedDict, Any
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_inverter_value_store
from modules.devices.zcs.zcs.config import ZCSInverterSetup


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class ZCSInverter(AbstractInverter):
    def __init__(self, component_config: ZCSInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        power = self.client.read_holding_registers(0x0485, ModbusDataType.INT_16, unit=self.__modbus_id)/100
        exported = self.client.read_holding_registers(0x0684, ModbusDataType.UINT_32, unit=self.__modbus_id)/100
        # exported = self.sim_counter.sim_count(power)[1]

        inverter_state = InverterState(
            # currents=currents,
            power=power,
            exported=exported
            # dc_power=dc_power
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=ZCSInverterSetup)
