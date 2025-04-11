#!/usr/bin/env python3
from typing import TypedDict, Any
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_inverter_value_store
from modules.devices.sample_request_by_device.sample_request_by_device.config import SampleInverterSetup


class KwargsDict(TypedDict):
    device_id: int


class SampleInverter(AbstractInverter):
    def __init__(self, component_config: SampleInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, response) -> None:
        # hier die Werte aus der response parsen
        power = response.get("power")
        currents = response.get("currents")
        dc_power = response.get("dc_power")
        exported = self.sim_counter.sim_count(power)[1]

        inverter_state = InverterState(
            currents=currents,
            power=power,
            exported=exported,
            dc_power=dc_power
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SampleInverterSetup)
