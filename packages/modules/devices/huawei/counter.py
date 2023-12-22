#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.huawei.config import HuaweiCounterSetup


class HuaweiCounter:
    def __init__(self,
                 device_id: int,
                 component_config: Union[Dict, HuaweiCounterSetup]) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(HuaweiCounterSetup, component_config)
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, counter_currents_reg, counter_power_reg):
        power = counter_power_reg * -1
        currents = [val / -100 for val in counter_currents_reg]

        imported, exported = self.sim_counter.sim_count(power)

        counter_state = CounterState(
            currents=currents,
            imported=imported,
            exported=exported,
            power=power
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=HuaweiCounterSetup)
