#!/usr/bin/env python3
from typing import Any, Dict, TypedDict

from modules.devices.batterx.batterx.config import BatterXExternalInverterSetup
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_inverter_value_store


class KwargsDict(TypedDict):
    device_id: int


class BatterXExternalInverter(AbstractInverter):
    def __init__(self, component_config: BatterXExternalInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def get_power(self, resp: Dict) -> float:
        return resp["2913"]["3"] * -1

    def update(self, resp: Dict) -> None:
        power = self.get_power(resp)

        _, exported = self.sim_counter.sim_count(power)

        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=BatterXExternalInverterSetup)
