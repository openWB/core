#!/usr/bin/env python3
from typing import TypedDict, Any

from pymodbus.constants import Endian
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_inverter_value_store
from modules.devices.solarmax.solarmax.config import SolarmaxMsInverterSetup


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class SolarmaxMsInverter(AbstractInverter):
    def __init__(self,
                 component_config: SolarmaxMsInverterSetup,
                 **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id
        power = self.client.read_input_registers(120, ModbusDataType.INT_32, device_id=unit, wordorder=Endian.Little) * -1
        _, exported = self.sim_counter.sim_count(power)

        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SolarmaxMsInverterSetup)
