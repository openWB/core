#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.lg.lg.config import LgBatSetup


class KwargsDict(TypedDict):
    device_id: int


class LgBat(AbstractBat):
    def __init__(self, component_config: LgBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, response) -> None:
        if 'batconv_power' in response['statistics']:
            power = float(response["statistics"]["batconv_power"])
            if response["direction"]["is_battery_discharging_"] == "1":
                power = power * -1
        else:
            power = float(response["statistics"]["batt_conv_power_01kW"]) * -100  # Home 15
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
