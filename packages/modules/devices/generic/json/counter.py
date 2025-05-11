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

    def _compile_jq_filters(self) -> None:
        config = self.component_config.configuration
        self.jq_power = jq.compile(config.jq_power)
        self.jq_powers = [jq.compile(p) for p in config.jq_powers] if all(config.jq_powers) else []
        self.jq_currents = [jq.compile(c) for c in config.jq_currents] if all(config.jq_currents) else []
        self.jq_imported = jq.compile(config.jq_imported) if config.jq_imported else None
        self.jq_exported = jq.compile(config.jq_exported) if config.jq_exported else None

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self._compile_jq_filters()
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, response) -> None:
        power = float(self.jq_power.input(response).first())

        powers = (
            [float(j.input(response).first()) for j in self.jq_powers]
            if len(self.jq_powers) == 3 else None
        )

        currents = (
            [float(j.input(response).first()) for j in self.jq_currents]
            if len(self.jq_currents) == 3 else None
        )

        if self.jq_imported is None or self.jq_exported is None:
            imported, exported = self.sim_counter.sim_count(power)
        else:
            imported = float(self.jq_imported.input(response).first())
            exported = float(self.jq_exported.input(response).first())

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            powers=powers,
            currents=currents
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=JsonCounterSetup)
