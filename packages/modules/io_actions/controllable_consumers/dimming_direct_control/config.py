from dataclasses import dataclass
from typing import Optional
from modules.io_actions.groups import ActionGroup


@dataclass
class DimmingDirectControlConfig:
    io_device: Optional[int] = None
    digital_input: Optional[str] = None
    cp_id: int = None


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
