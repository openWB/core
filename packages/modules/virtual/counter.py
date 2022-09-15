#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.virtual.config import VirtualCounterSetup


class VirtualCounter:

    def __init__(self, device_id: int, component_config: Union[Dict, VirtualCounterSetup]) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(VirtualCounterSetup, component_config)
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id, add_child_values=True)
        self.component_info = ComponentInfo.from_component_config(self.component_config)

    def update(self):
        imported, exported = self.sim_counter.sim_count(self.component_config.configuration.external_consumption)

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=self.component_config.configuration.external_consumption,
            currents=[self.component_config.configuration.external_consumption/3/230]*3
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=VirtualCounterSetup)
