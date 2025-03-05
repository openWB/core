#!/usr/bin/env python3
from typing import Optional
from modules.common.abstract_device import AbstractBat
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.component_type import ComponentDescriptor
from modules.devices.generic.mqtt.config import MqttBatSetup


class MqttBat(AbstractBat):
    def __init__(self, component_config: MqttBatSetup) -> None:
        self.component_config = component_config

    def initialize(self) -> None:
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        # wird bereits in Regelung gesetzt, eigene Implementierung notwendig, um zu erkennen,
        # ob der Speicher die Funktion bietet
        pass


component_descriptor = ComponentDescriptor(configuration_factory=MqttBatSetup)
