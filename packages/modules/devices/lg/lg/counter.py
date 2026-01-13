#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.lg.lg.config import LgCounterSetup


class KwargsDict(TypedDict):
    device_id: int


class LgCounter(AbstractCounter):
    def __init__(self, component_config: LgCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, response) -> None:
        if 'grid_power' in response['statistics']:
            power = float(response["statistics"]["grid_power"])
            if response["direction"]["is_grid_selling_"] == "1":
                power = power*-1
        else:
            power = float(response["statistics"]["grid_power_01kW"]) * 100  # Home 15

        if response["direction"]["is_grid_selling_"] == "1":
            power = power*-1
        imported, exported = self.sim_counter.sim_count(power)
        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=LgCounterSetup)
