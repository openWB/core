#!/usr/bin/env python3
from modules.common.abstract_device import AbstractCounter
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.component_type import ComponentDescriptor
from modules.devices.generic.mqtt.config import MqttCounterSetup


class MqttCounter(AbstractCounter):
    def __init__(self, component_config: MqttCounterSetup) -> None:
        self.component_config = component_config

    def initialize(self) -> None:
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))


component_descriptor = ComponentDescriptor(configuration_factory=MqttCounterSetup)
