#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.lg.lg.config import LgBatSetup


class LgBat(AbstractBat):
    def __init__(self, device_id: int, component_config: Union[Dict, LgBatSetup]) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(LgBatSetup, component_config)
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, response) -> None:
        power = float(response["statistics"]["batconv_power"])
        if response["direction"]["is_battery_discharging_"] == "1":
            power = power * -1
        try:
            soc = float(response["statistics"]["bat_user_soc"])
        except ValueError:
            self.fault_state.warning('Speicher-SOC ist nicht numerisch und wird auf 0 gesetzt.')
            soc = 0

        imported, exported = self.sim_counter.sim_count(power)
        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=LgBatSetup)
