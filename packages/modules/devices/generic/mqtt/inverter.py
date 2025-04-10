#!/usr/bin/env python3
from typing import Any, Dict, TypedDict

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
        power = received_topics.get(f"openWB/mqtt/pv/{self.component_config.id}/get/power")
        if received_topics.get(f"openWB/mqtt/pv/{self.component_config.id}/get/exported"):
            exported = received_topics.get(f"openWB/mqtt/pv/{self.component_config.id}/get/exported")
        else:
            exported = self.sim_counter.sim_count(power)[1]

        inverter_state = InverterState(
            currents=received_topics.get(f"openWB/mqtt/pv/{self.component_config.id}/get/currents"),
            power=power,
            exported=exported,
            dc_power=received_topics.get(f"openWB/mqtt/pv/{self.component_config.id}/get/dc_power")
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=MqttInverterSetup)
