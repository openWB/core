#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.solakon.solakon_one.config import SolakonOneCounterSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class SolakonOneCounter(AbstractCounter):
    def __init__(self, component_config: SolakonOneCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(
            self.kwargs['device_id'], self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.COUNTER, self.component_config.id, self.fault_state)

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id

        # Reg 39168 Meter collection Active power, laut Hersteller-Doku > 0 Einspeisung, < 0 Netzbezug
        power = self.client.read_holding_registers(39168, ModbusDataType.INT_32, unit=unit) * -1

        self.peak_filter.check_values(power)
        imported, exported = self.sim_counter.sim_count(power)
        counter_state = CounterState(
            power=power,
            imported=imported,
            exported=exported
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SolakonOneCounterSetup)
