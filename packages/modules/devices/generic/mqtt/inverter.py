#!/usr/bin/env python3
from typing import Any, Dict, TypedDict

from helpermodules.utils._get_default import get_default
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.component_type import ComponentDescriptor
from modules.common.simcount._simcounter import SimCounter
from modules.common.store._inverter import get_inverter_value_store
from modules.devices.generic.mqtt.config import MqttInverterSetup


class KwargsDict(TypedDict):
    device_id: int


class MqttInverter(AbstractInverter):
    def __init__(self, component_config: MqttInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.sim_counter = SimCounter(self.kwargs['device_id'], self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)

    def update(self, received_topics: Dict) -> None:
        def parse_received_topics(value: str):
            return received_topics.get(f"{topic_prefix}{value}", get_default(InverterState, value))
        # [] für erforderliche Topics, .get() für optionale Topics
        topic_prefix = f"openWB/mqtt/pv/{self.component_config.id}/get/"
        power = received_topics[f"{topic_prefix}power"]

        if received_topics.get(f"{topic_prefix}exported") is None or received_topics.get(f"{topic_prefix}imported") is None:
            imported, exported = self.sim_counter.sim_count(power)
        if received_topics.get(f"{topic_prefix}exported"):
            exported = received_topics[f"{topic_prefix}exported"]
        if received_topics.get(f"{topic_prefix}imported"):
            imported = received_topics[f"{topic_prefix}imported"]

        currents = parse_received_topics("currents")
        dc_power = parse_received_topics("dc_power")

        inverter_state = InverterState(
            currents=currents,
            power=power,
            exported=exported,
            imported=imported,
            dc_power=dc_power
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=MqttInverterSetup)
