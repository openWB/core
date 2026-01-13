#!/usr/bin/env python3
from typing import TypedDict, Any
from modules.common import req
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.sample_request_by_component.sample_request_by_component.config import SampleCounterSetup


class KwargsDict(TypedDict):
    device_id: int
    ip_address: str


class SampleCounter(AbstractCounter):
    def __init__(self, component_config: SampleCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.ip_address: str = self.kwargs['ip_address']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        resp = req.get_http_session().get(self.ip_address)
        power = resp.json().get("power")
        imported, exported = self.sim_counter.sim_count(power)

        counter_state = CounterState(
            currents=currents,
            imported=imported,
            exported=exported,
            power=power,
            frequency=frequency,
            power_factors=power_factors,
            powers=powers,
            voltages=voltages
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SampleCounterSetup)
