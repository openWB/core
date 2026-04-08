#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.vzlogger.vzlogger.config import VZLoggerCounterSetup
from modules.devices.vzlogger.vzlogger.utils import parse_line
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType


class KwargsDict(TypedDict):
    device_id: int


class VZLoggerCounter(AbstractCounter):
    def __init__(self, component_config: VZLoggerCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.COUNTER, self.component_config.id, self.fault_state)

    def update(self, response):
        config = self.component_config.configuration

        power = parse_line(response, config.line_power)
        if config.line_imported is None or config.line_exported is None:
            self.peak_filter.check_values(power)
            imported, exported = self.sim_counter.sim_count(power)
        else:
            imported = parse_line(response, config.line_imported)
            exported = parse_line(response, config.line_exported)
            imported, exported = self.peak_filter.check_values(power, imported, exported)

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=VZLoggerCounterSetup)
