#!/usr/bin/env python3
from typing import Any, TypedDict

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.solar_world.solar_world.config import SolarWorldCounterSetup


class KwargsDict(TypedDict):
    device_id: int


class SolarWorldCounter(AbstractCounter):
    def __init__(self, component_config: SolarWorldCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, response):
        power = response["PowerIn"] - response["PowerOut"]
        imported, exported = self.sim_counter.sim_count(power)

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SolarWorldCounterSetup)
