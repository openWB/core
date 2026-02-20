#!/usr/bin/env python3
from typing import Any, TypedDict

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, Endian, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_inverter_value_store
from modules.devices.sungrow.sungrow_micro.config import SungrowMicroInverterSetup, SungrowMicro


class KwargsDict(TypedDict):
    client: ModbusTcpClient_
    device_config: SungrowMicro


class SungrowMicroInverter(AbstractInverter):
    def __init__(self, component_config: SungrowMicroInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.device_config: SungrowMicro = self.kwargs['device_config']
        self.__tcp_client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.device_config.id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> float:
        unit = self.device_config.configuration.modbus_id

        power = self.__tcp_client.read_input_registers(32213, ModbusDataType.UINT_32,
                                                       wordorder=Endian.Little, unit=unit) * -1

        imported, exported = self.sim_counter.sim_count(power)

        inverter_state = InverterState(
            power=power,
            imported=imported,
            exported=exported
        )
        self.store.set(inverter_state)
        return power


component_descriptor = ComponentDescriptor(configuration_factory=SungrowMicroInverterSetup)
