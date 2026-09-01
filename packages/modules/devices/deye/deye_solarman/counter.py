#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
# from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.common.utils.peak_filter import PeakFilter
from modules.devices.deye.deye_solarman.config import DeyeSolarmanCounterSetup
from modules.devices.deye.deye_solarman.device_type import DeviceType
from modules.common.component_type import ComponentType
from pysolarmanv5 import PySolarmanV5 as ModbusSolarmanClient_


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusSolarmanClient_


class DeyeSolarmanCounter(AbstractCounter):
    def __init__(self, component_config: DeyeSolarmanCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: ModbusSolarmanClient_ = self.kwargs['client']
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.COUNTER, self.component_config.id, self.fault_state)
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.device_type = DeviceType(self.client.read_holding_registers(0, 1)[0])

    def update(self):
        if self.device_type == DeviceType.SINGLE_PHASE_STRING or self.device_type == DeviceType.SINGLE_PHASE_HYBRID:
            frequency = self.client.read_holding_registers(79, 1)[0] / 100

            if self.device_type == DeviceType.SINGLE_PHASE_HYBRID:
                powers = [0]*3
                currents = [0]*3
                voltages = [0]*3
                power = 0

            elif self.device_type == DeviceType.SINGLE_PHASE_STRING:
                currents = [c / 100 for c in self.client.read_holding_registers(76, 3)]
                voltages = [v / 10 for v in self.client.read_holding_registers(70, 3)]
                powers = [currents[i] * voltages[i] for i in range(0, 3)]
                power = sum(powers)

        else:  # THREE_PHASE_LV (0x0500, 0x0005), THREE_PHASE_HV (0x0006)
            currents = [c / 100 for c in self.client.read_holding_registers(613, 3)]
            voltages = [v / 10 for v in self.client.read_holding_registers(644, 3)]
            powers = self.client.read_holding_registers(616, 3)
            power = sum(powers)
            frequency = self.client.read_holding_registers(609, 1)[0] / 100

        self.peak_filter.check_values(power)
        imported, exported = self.sim_counter.sim_count(power)
        counter_state = CounterState(
            currents=currents,
            voltages=voltages,
            powers=powers,
            power=power,
            imported=imported,
            exported=exported,
            frequency=frequency
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=DeyeSolarmanCounterSetup)
