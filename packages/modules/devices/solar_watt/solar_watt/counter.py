#!/usr/bin/env python3
import logging
from typing import Any, Dict, Union, TypedDict

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.solar_watt.solar_watt.api import parse_value
from modules.devices.solar_watt.solar_watt.config import SolarWattCounterSetup

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int


class SolarWattCounter(AbstractCounter):
    def __init__(self, component_config: Union[Dict, SolarWattCounterSetup], **kwargs: Any) -> None:
        self.component_config = SolarWattCounterSetup(**component_config)
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, response: Dict, energy_manager: bool) -> None:
        if energy_manager:
            power_consumed = parse_value(response, "PowerConsumedFromGrid")
            power_out = parse_value(response, "PowerOut")
            power = power_consumed - power_out
        else:
            power = int(response["FData"]["PGrid"])
        imported, exported = self.sim_counter.sim_count(power)
        self.store.set(CounterState(
            imported=imported,
            exported=exported,
            power=power
        ))


component_descriptor = ComponentDescriptor(configuration_factory=SolarWattCounterSetup)
