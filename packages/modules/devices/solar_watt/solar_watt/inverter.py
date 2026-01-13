#!/usr/bin/env python3
import logging
from typing import Any, Dict, TypedDict

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.solar_watt.solar_watt.api import parse_value
from modules.devices.solar_watt.solar_watt.config import SolarWattInverterSetup

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int


class SolarWattInverter(AbstractInverter):
    def __init__(self, component_config: SolarWattInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, response: Dict) -> None:
        power = parse_value(response, "PowerProduced") * -1
        _, exported = self.sim_counter.sim_count(power)
        self.store.set(InverterState(
            exported=exported,
            power=power
        ))


component_descriptor = ComponentDescriptor(configuration_factory=SolarWattInverterSetup)
