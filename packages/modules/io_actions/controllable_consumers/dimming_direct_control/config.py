from dataclasses import dataclass, field
from typing import Dict, List, Optional
from dataclass_utils.factories import empty_io_pattern_factory, empty_list_factory
from modules.io_actions.groups import ActionGroup


@dataclass
class DimmingDirectControlConfig:
    io_device: Optional[int] = None
    input_pattern: List[Dict] = field(default_factory=empty_io_pattern_factory)
    devices: List[List[str, str]] = field(default_factory=empty_list_factory)


class DimmingDirectControlSetup:
    def __init__(self,
                 name: str = "Dimmen per Direktsteuerung",
                 type: str = "dimming_direct_control",
                 id: int = 0,
                 configuration: DimmingDirectControlConfig = None):
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or DimmingDirectControlConfig()
        self.group = ActionGroup.CONTROLLABLE_CONSUMERS.value
