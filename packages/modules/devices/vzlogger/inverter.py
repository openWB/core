#!/usr/bin/env python3
from dataclass_utils import dataclass_from_dict
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo
from modules.common.store import get_inverter_value_store
from modules.devices.vzlogger.config import VZLoggerInverterSetup
from modules.devices.vzlogger.utils import parse_line


class VZLoggerInverter:
    def __init__(self, component_config: VZLoggerInverterSetup) -> None:
        self.component_config = dataclass_from_dict(VZLoggerInverterSetup, component_config)
        self.store = get_inverter_value_store(self.component_config.id)
        self.component_info = ComponentInfo.from_component_config(self.component_config)

    def update(self, response) -> None:
        inverter_state = InverterState(
            power=parse_line(response, self.component_config.configuration.line_power),
            exported=parse_line(response, self.component_config.configuration.line_exported),
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=VZLoggerInverterSetup)
