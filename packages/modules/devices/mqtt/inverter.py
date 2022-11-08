#!/usr/bin/env python3
from typing import Dict, Union
from modules.common.fault_state import ComponentInfo

from dataclass_utils import dataclass_from_dict
from modules.common.component_type import ComponentDescriptor
from modules.devices.mqtt.config import MqttInverterSetup


class MqttInverter:
    def __init__(self, component_config: Union[Dict, MqttInverterSetup]) -> None:
        self.component_config = dataclass_from_dict(MqttInverterSetup, component_config)
        self.component_info = ComponentInfo.from_component_config(self.component_config)


component_descriptor = ComponentDescriptor(configuration_factory=MqttInverterSetup)
