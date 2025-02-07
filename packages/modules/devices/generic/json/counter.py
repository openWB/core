#!/usr/bin/env python3
from typing import TypedDict, Any
import jq

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount._simcounter import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.generic.json.config import JsonCounterSetup


class KwargsDict(TypedDict):
    device_id: int


class JsonCounter(AbstractCounter):
    def __init__(self, component_config: JsonCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, response) -> None:
        config = self.component_config.configuration

        power = float(jq.compile(config.jq_power).input(response).first())

        if all(config.jq_powers):
            powers = [float(jq.compile(p).input(response).first()) for p in config.jq_powers]
        else:
            powers = None

        if all(config.jq_currents):
            currents = [float(jq.compile(c).input(response).first()) for c in config.jq_currents]
        else:
            currents = None

        if config.jq_imported is None or config.jq_exported is None:
            imported, exported = self.sim_counter.sim_count(power)
        else:
            imported = float(jq.compile(config.jq_imported).input(response).first())
            exported = float(jq.compile(config.jq_exported).input(response).first())

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            powers=powers,
            currents=currents
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=JsonCounterSetup)
