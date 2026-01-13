#!/usr/bin/env python3
from typing import Dict, TypedDict, Any

from modules.devices.batterx.batterx.config import BatterXInverterSetup
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store


class KwargsDict(TypedDict):
    device_id: int


class BatterXInverter(AbstractInverter):
    def __init__(self, component_config: BatterXInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def get_power(self, resp: Dict) -> float:
        return resp["1634"]["0"] * -1

    def get_inverter_state(self, power: float) -> InverterState:
        _, exported = self.sim_counter.sim_count(power)

        return InverterState(
            power=power,
            exported=exported
        )

    def update(self, resp: Dict) -> None:
        self.store.set(self.get_inverter_state(self.get_power(resp)))


component_descriptor = ComponentDescriptor(configuration_factory=BatterXInverterSetup)
