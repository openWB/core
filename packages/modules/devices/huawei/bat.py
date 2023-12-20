#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.huawei.config import HuaweiBatSetup


class HuaweiBat:
    def __init__(self,
                 device_id: int,
                 component_config: Union[Dict, HuaweiBatSetup]) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(HuaweiBatSetup, component_config)
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, bat_power_reg, bat_soc_reg) -> None:
        soc = bat_soc_reg / 10

        imported, exported = self.sim_counter.sim_count(bat_power_reg)
        bat_state = BatState(
            power=bat_power_reg,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=HuaweiBatSetup)
