#!/usr/bin/env python3
from requests import Session
from typing import TypedDict, Any
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.mystrom.mystrom.config import MystromCounterSetup


class KwargsDict(TypedDict):
    device_id: int
    ip_address: str


class MystromCounter(AbstractCounter):
    def __init__(self, component_config: MystromCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.ip_address: str = self.kwargs['ip_address']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, session: Session):
        resp = session.get(f"http://{self.ip_address}/report").json()
        power = resp["power"]
        imported, exported = self.sim_counter.sim_count(power)

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=MystromCounterSetup)
