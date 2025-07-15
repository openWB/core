#!/usr/bin/env python3
from typing import Any, Dict, TypedDict

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.component_type import ComponentDescriptor
from modules.common.simcount._simcounter import SimCounter
from modules.common.store._counter import get_counter_value_store
from modules.devices.generic.mqtt.config import MqttCounterSetup


class KwargsDict(TypedDict):
    device_id: int


class MqttCounter(AbstractCounter):
    def __init__(self, component_config: MqttCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.sim_counter = SimCounter(self.kwargs['device_id'], self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)

    def update(self, received_topics: Dict) -> None:
        # [] für erforderliche Topics, .get() für optionale Topics
        currents = received_topics.get(f"openWB/mqtt/counter/{self.component_config.id}/get/currents")
        power = received_topics[f"openWB/mqtt/counter/{self.component_config.id}/get/power"]
        frequency = received_topics.get(f"openWB/mqtt/counter/{self.component_config.id}/get/frequency")
        power_factors = received_topics.get(f"openWB/mqtt/counter/{self.component_config.id}/get/power_factors")
        powers = received_topics.get(f"openWB/mqtt/counter/{self.component_config.id}/get/powers")
        voltages = received_topics.get(f"openWB/mqtt/counter/{self.component_config.id}/get/voltages")
        if (received_topics.get(f"openWB/mqtt/counter/{self.component_config.id}/get/imported") and
                received_topics.get(f"openWB/mqtt/counter/{self.component_config.id}/get/exported")):
            imported = received_topics.get(f"openWB/mqtt/counter/{self.component_config.id}/get/imported")
            exported = received_topics.get(f"openWB/mqtt/counter/{self.component_config.id}/get/exported")
        else:
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


component_descriptor = ComponentDescriptor(configuration_factory=MqttCounterSetup)
