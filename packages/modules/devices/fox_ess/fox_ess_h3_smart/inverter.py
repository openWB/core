#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.utils.peak_filter import PeakFilter
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.fox_ess.fox_ess_h3_smart.config import FoxEssH3SmartInverterSetup
from modules.common.component_type import ComponentType


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class FoxEssH3SmartInverter(AbstractInverter):
    def __init__(self, component_config: FoxEssH3SmartInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.INVERTER, self.component_config.id, self.fault_state)
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id

        pv_strings = self.client.read_holding_registers(39279, [ModbusDataType.INT_32]*6, unit=unit)
        power = sum(pv_strings) * -1

        self.peak_filter.check_values(power)
        _, exported = self.sim_counter.sim_count(power)
        inverter_state = InverterState(
            power=power,
            exported=exported,
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=FoxEssH3SmartInverterSetup)
