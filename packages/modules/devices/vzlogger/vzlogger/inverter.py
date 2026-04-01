#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_inverter_value_store
from modules.devices.vzlogger.vzlogger.config import VZLoggerInverterSetup
from modules.devices.vzlogger.vzlogger.utils import parse_line
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType


class KwargsDict(TypedDict):
    device_id: int


class VZLoggerInverter(AbstractInverter):
    def __init__(self, component_config: VZLoggerInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.INVERTER, self.component_config.id, self.fault_state)

    def update(self, response) -> None:
        config = self.component_config.configuration

        power = parse_line(response, config.line_power)
        if config.line_exported is None:
            self.peak_filter.check_values(power)
            _, exported = self.sim_counter.sim_count(power)
        else:
            exported = parse_line(response, config.line_exported)
            _, exported = self.peak_filter.check_values(power, None, exported)

        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=VZLoggerInverterSetup)
