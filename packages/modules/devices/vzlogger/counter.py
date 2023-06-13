#!/usr/bin/env python3
from dataclass_utils import dataclass_from_dict
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo
from modules.common.store import get_counter_value_store
from modules.devices.vzlogger.config import VZLoggerCounterSetup
from modules.devices.vzlogger.utils import parse_line


class VZLoggerCounter:
    def __init__(self, component_config: VZLoggerCounterSetup) -> None:
        self.component_config = dataclass_from_dict(VZLoggerCounterSetup, component_config)
        self.store = get_counter_value_store(self.component_config.id)
        self.component_info = ComponentInfo.from_component_config(self.component_config)

    def update(self, response):
        counter_state = CounterState(
            imported=parse_line(response, self.component_config.configuration.line_imported),
            exported=parse_line(response, self.component_config.configuration.line_exported),
            power=parse_line(response, self.component_config.configuration.line_power),
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=VZLoggerCounterSetup)
