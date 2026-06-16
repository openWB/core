#!/usr/bin/env python3
from typing import Any, TypedDict

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.generic.virtual.config import VirtualCounterSetup


class KwargsDict(TypedDict):
    device_id: int


class VirtualCounter(AbstractCounter):
    def __init__(self, component_config: VirtualCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type,
                                               self.component_config.id,
                                               add_child_values=True,
                                               simcounter=self.sim_counter)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        counter_state = CounterState(
            imported=None,
            exported=None,
            power=self.component_config.configuration.external_consumption,
            currents=[self.component_config.configuration.external_consumption/3/230]*3
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=VirtualCounterSetup)
