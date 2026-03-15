#!/usr/bin/env python3
from typing import Any, TypedDict

from modules.devices.algodue.algodue.config import AlgodueInverterSetup
from modules.common import modbus
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_inverter_value_store


class KwargsDict(TypedDict):
    device_id: int
    tcp_client: modbus.ModbusTcpClient_
    modbus_id: int


class AlgodueInverter(AbstractInverter):
    def __init__(self, component_config: AlgodueInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['tcp_client']
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        currents = self.__tcp_client.read_input_registers(
            0x100E, [ModbusDataType.FLOAT_32]*3, unit=self.__modbus_id)
        powers = self.__tcp_client.read_input_registers(0x1020, [ModbusDataType.FLOAT_32]*3, unit=self.__modbus_id)
        power = sum(powers)

        _, exported = self.sim_counter.sim_count(power)

        inverter_state = InverterState(
            power=power,
            currents=currents,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=AlgodueInverterSetup)
