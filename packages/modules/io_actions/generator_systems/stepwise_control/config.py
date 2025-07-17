from dataclasses import dataclass
from typing import Optional
from modules.io_actions.groups import ActionGroup


@dataclass
class StepwiseControlConfig:
    io_device: Optional[int] = None
    s1: str = None
    s2: str = None
    w3: str = None
    pv_id: int = None


class StepwiseControlSetup:
    def __init__(self,
                 name: str = "Stufenweise Steuerung einer EZA",
                 type: str = "stepwise_control",
                 id: int = 0,
                 configuration: StepwiseControlConfig = None):
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or StepwiseControlConfig()
        self.group = ActionGroup.GENERATOR_SYSTEMS.value
