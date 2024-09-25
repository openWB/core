#!/usr/bin/env python3
from dataclass_utils import dataclass_from_dict
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.vzlogger.vzlogger.config import VZLoggerCounterSetup
from modules.devices.vzlogger.vzlogger.utils import parse_line


class VZLoggerCounter(AbstractCounter):
    def __init__(self, device_id: int, component_config: VZLoggerCounterSetup) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(VZLoggerCounterSetup, component_config)
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, response):
        config = self.component_config.configuration

        power = parse_line(response, config.line_power)
        if config.line_imported is None or config.line_exported is None:
            imported, exported = self.sim_counter.sim_count(power)
        else:
            imported = parse_line(response, config.line_imported)
            exported = parse_line(response, config.line_exported)

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=VZLoggerCounterSetup)
