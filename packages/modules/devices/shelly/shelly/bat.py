#!/usr/bin/env python3
import logging
from typing import Optional, TypedDict, Any
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_component_value_store
from modules.common.simcount._simcounter import SimCounter
from modules.devices.shelly.shelly.config import ShellyBatSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType
from modules.devices.shelly.shelly.status_handler import parse_data, request_status

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    ip_address: str
    factor: int
    phase: int
    generation: Optional[int]


class ShellyBat(AbstractBat):
    def __init__(self, component_config: ShellyBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.address: str = self.kwargs['ip_address']
        self.factor: int = self.kwargs['factor']
        self.phase: int = self.kwargs['phase']
        self.generation: Optional[int] = self.kwargs['generation']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.BAT, self.component_config.id, self.fault_state)

    def update(self) -> None:
        status = request_status(self.address, self.generation)
        _, _, currents, _, power, _ = parse_data(self.phase, self.factor, status)
        self.peak_filter.check_values(power)
        imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            power=power,
            currents=currents,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=ShellyBatSetup)
