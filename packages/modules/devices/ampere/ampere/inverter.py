#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_inverter_value_store
from modules.devices.ampere.ampere.config import AmpereInverterSetup


class KwargsDict(TypedDict):
    device_id: int
    modbus_id: int
    client: ModbusTcpClient_


class AmpereInverter(AbstractInverter):
    def __init__(self,
                 component_config: AmpereInverterSetup,
                 **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.modbus_id: int = self.kwargs['modbus_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        pv1_power = self.client.read_holding_registers(519, ModbusDataType.INT_16, device_id=self.modbus_id) * -1
        pv2_power = self.client.read_holding_registers(522, ModbusDataType.INT_16, device_id=self.modbus_id) * -1

        power = pv1_power + pv2_power

        _, exported = self.sim_counter.sim_count(power)
        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=AmpereInverterSetup)
