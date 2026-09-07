#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.ecoflow.stream.config import EcoflowStreamBatSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType


class KwargsDict(TypedDict):
    device_id: int


class EcoflowStreamBat(AbstractBat):
    def __init__(self, component_config: EcoflowStreamBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.BAT, self.component_config.id, self.fault_state)

    def update(self, response) -> None:
        power = float(response['data']['powGetBpCms'])
        soc = float(response['data']['cmsBattSoc'])

        self.peak_filter.check_values(power)
        imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=EcoflowStreamBatSetup)
