from dataclasses import dataclass, field
from typing import Dict, List, Optional
from dataclass_utils.factories import empty_list_factory, empty_io_pattern_stepwise_factory
from modules.io_actions.groups import ActionGroup


@dataclass
class StepwiseControlConfig:
    io_device: Optional[int] = None
    input_pattern: List[Dict] = field(default_factory=empty_io_pattern_stepwise_factory)
    devices: List[Dict] = field(default_factory=empty_list_factory)
    # [{"type": "inverter", "id": 1},...]
    passthrough_enabled: bool = False
    output_pattern: List[Dict] = field(default_factory=empty_io_pattern_stepwise_factory)


class StepwiseControlSetup:
    def __init__(self,
                 name: str = "Stufenweise Steuerung von EZA",
                 type: str = "stepwise_control",
                 id: int = 0,
                 configuration: StepwiseControlConfig = None):
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or StepwiseControlConfig()
        self.group = ActionGroup.GENERATOR_SYSTEMS.value
