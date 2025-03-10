#!/usr/bin/env python3
from typing import TypedDict, Any
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.sample_request_by_device.config import SampleCounterSetup


class KwargsDict(TypedDict):
    device_id: int


class SampleCounter(AbstractCounter):
    def __init__(self, component_config: SampleCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, response):
        # hier die Werte aus der response parsen
        power = response.get("power")
        currents = response.get("currents")
        frequency = response.get("frequency")
        power_factors = response.get("power_factors")
        powers = response.get("powers")
        voltages = response.get("voltages")
        imported, exported = self.sim_counter.sim_count(power)

        counter_state = CounterState(
            currents=currents,
            imported=imported,
            exported=exported,
            power=power,
            frequency=frequency,
            power_factors=power_factors,
            powers=powers,
            voltages=voltages
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SampleCounterSetup)
