#!/usr/bin/env python3
import logging
from typing import Optional, TypedDict, Any
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_component_value_store
from modules.common.simcount._simcounter import SimCounter
from modules.devices.shelly.shelly.config import ShellyCounterSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType
from modules.devices.shelly.shelly.status_handler import parse_data, request_status

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    ip_address: str
    factor: int
    phase: int
    generation: Optional[int]


class ShellyCounter(AbstractCounter):
    def __init__(self, component_config: ShellyCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.address: str = self.kwargs['ip_address']
        self.factor: int = self.kwargs['factor']
        self.phase: int = self.kwargs['phase']
        self.generation: Optional[int] = self.kwargs['generation']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.COUNTER, self.component_config.id, self.fault_state)

    def get_data(self) -> CounterState:
        power = 0
        status = request_status(self.address, self.generation)
        powers, voltages, currents, power_factors, power, frequency = parse_data(self.phase, self.factor, status)
        self.peak_filter.check_values(power)
        imported, exported = self.sim_counter.sim_count(power)

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            powers=powers,
            power=power
        )
        if 'frequency' in locals():
            counter_state.frequency = frequency
        if "power_factors" in locals():
            counter_state.power_factors = power_factors
        if "voltages" in locals():
            counter_state.voltages = voltages
        if "currents" in locals():
            counter_state.currents = currents

    def update(self) -> None:
        counter_state = self.get_data()
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=ShellyCounterSetup)
