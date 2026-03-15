#!/usr/bin/env python3
from typing import Any, Dict, Optional, TypedDict

from helpermodules.pub import Pub
from helpermodules.utils._get_default import get_default
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.component_type import ComponentDescriptor
from modules.common.simcount._simcounter import SimCounter
from modules.common.store._battery import get_bat_value_store
from modules.devices.generic.mqtt.config import MqttBatSetup


class KwargsDict(TypedDict):
    device_id: int


class MqttBat(AbstractBat):
    def __init__(self, component_config: MqttBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.sim_counter = SimCounter(self.kwargs['device_id'], self.component_config.id, prefix="bat")
        self.store = get_bat_value_store(self.component_config.id)

    def update(self, received_topics: Dict) -> None:
        def parse_received_topics(value: str):
            return received_topics.get(f"{topic_prefix}{value}", get_default(BatState, value))
        # [] für erforderliche Topics, .get() für optionale Topics
        topic_prefix = f"openWB/mqtt/bat/{self.component_config.id}/get/"
        currents = parse_received_topics("currents")
        power = received_topics[f"{topic_prefix}power"]
        soc = received_topics[f"{topic_prefix}soc"]
        if (received_topics.get(f"{topic_prefix}imported") is not None and
                received_topics.get(f"{topic_prefix}exported") is not None):
            imported = received_topics[f"{topic_prefix}imported"]
            exported = received_topics[f"{topic_prefix}exported"]
        else:
            imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            currents=currents,
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        Pub().pub(f"openWB/set/mqtt/bat/{self.component_config.id}/set/power_limit", power_limit)

    def power_limit_controllable(self) -> bool:
        return self.component_config.configuration.power_limit_controllable


component_descriptor = ComponentDescriptor(configuration_factory=MqttBatSetup)
