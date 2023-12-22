#!/usr/bin/env python3
from typing import Dict, Union
from modules.common.fault_state import ComponentInfo, FaultState

from dataclass_utils import dataclass_from_dict
from modules.common.component_type import ComponentDescriptor
from modules.devices.mqtt.config import MqttBatSetup


class MqttBat:
    def __init__(self, component_config: Union[Dict, MqttBatSetup]) -> None:
        self.component_config = dataclass_from_dict(MqttBatSetup, component_config)
        self.fault_state = FaultState(ComponentInfo.from_component_config(component_config))


component_descriptor = ComponentDescriptor(configuration_factory=MqttBatSetup)
