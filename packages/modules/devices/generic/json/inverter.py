#!/usr/bin/env python3
from typing import TypedDict, Any
import jq

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_inverter_value_store
from modules.devices.generic.json.config import JsonInverterSetup


class KwargsDict(TypedDict):
    device_id: int


class JsonInverter(AbstractInverter):
    def __init__(self, component_config: JsonInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def _compile_jq_filters(self) -> None:
        config = self.component_config.configuration
        self.jq_power = jq.compile(config.jq_power)
        self.jq_exported = jq.compile(config.jq_exported) if config.jq_exported else None
        self.jq_currents = [jq.compile(c) for c in config.jq_currents] if all(config.jq_currents) else None

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self._compile_jq_filters()
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, response) -> None:
        power = float(self.jq_power.input(response).first())
        if power >= 0:
            power = power * -1

        currents = (
            [float(j.input(response).first()) for j in self.jq_currents]
            if self.jq_currents is not None else None
        )

        if self.jq_exported is None:
            _, exported = self.sim_counter.sim_count(power)
        else:
            exported = float(self.jq_exported.input(response).first())

        inverter_state = InverterState(
            power=power,
            exported=exported,
            currents=currents
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=JsonInverterSetup)
